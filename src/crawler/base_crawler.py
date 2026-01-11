"""
Base Async Crawler with Resume Capability
SEG301 - Milestone 1: Data Acquisition
"""

import asyncio
import aiohttp
import aiofiles
import orjson
import logging
import time
import random
from abc import ABC, abstractmethod
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any, Set
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm.asyncio import tqdm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AsyncCrawler(ABC):
    """
    Base async crawler with:
    - Concurrent request management (semaphore)
    - Rate limiting
    - Checkpoint/Resume capability
    - User-agent rotation
    - Retry with exponential backoff
    """
    
    def __init__(
        self,
        name: str,
        output_dir: str = "data",
        max_concurrent: int = 50,
        rate_limit: float = 0.1,  # seconds between requests
        checkpoint_interval: int = 100,  # save checkpoint every N items
        timeout: int = 30
    ):
        self.name = name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_concurrent = max_concurrent
        self.rate_limit = rate_limit
        self.checkpoint_interval = checkpoint_interval
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        
        self.ua = UserAgent()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Progress tracking
        self.crawled_urls: Set[str] = set()
        self.failed_urls: List[str] = []
        self.results: List[Dict[str, Any]] = []
        self.total_crawled = 0
        
        # Checkpoint file
        self.checkpoint_file = self.output_dir / f"{name}_checkpoint.json"
        
    def get_headers(self) -> Dict[str, str]:
        """Get request headers with random user-agent"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    async def init_session(self):
        """Initialize aiohttp session"""
        if self.session is None:
            connector = aiohttp.TCPConnector(
                limit=self.max_concurrent,
                limit_per_host=20,
                ttl_dns_cache=300
            )
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout
            )
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
            self.session = None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30)
    )
    async def fetch(self, url: str) -> Optional[str]:
        """Fetch URL with rate limiting and retry"""
        async with self.semaphore:
            await asyncio.sleep(self.rate_limit + random.uniform(0, 0.1))
            
            try:
                async with self.session.get(url, headers=self.get_headers()) as response:
                    if response.status == 200:
                        return await response.text()
                    elif response.status == 429:  # Rate limited
                        logger.warning(f"Rate limited on {url}, waiting...")
                        await asyncio.sleep(10)
                        raise Exception("Rate limited")
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return None
            except asyncio.TimeoutError:
                logger.error(f"Timeout fetching {url}")
                raise
            except Exception as e:
                logger.error(f"Error fetching {url}: {e}")
                raise
    
    async def save_checkpoint(self):
        """Save current progress to checkpoint file"""
        checkpoint = {
            'crawled_urls': list(self.crawled_urls),
            'failed_urls': self.failed_urls,
            'total_crawled': self.total_crawled,
            'timestamp': datetime.now().isoformat()
        }
        async with aiofiles.open(self.checkpoint_file, 'wb') as f:
            await f.write(orjson.dumps(checkpoint))
        logger.info(f"Checkpoint saved: {self.total_crawled} items")
    
    async def load_checkpoint(self) -> bool:
        """Load checkpoint if exists"""
        if self.checkpoint_file.exists():
            try:
                async with aiofiles.open(self.checkpoint_file, 'rb') as f:
                    content = await f.read()
                    checkpoint = orjson.loads(content)
                    self.crawled_urls = set(checkpoint.get('crawled_urls', []))
                    self.failed_urls = checkpoint.get('failed_urls', [])
                    self.total_crawled = checkpoint.get('total_crawled', 0)
                    logger.info(f"Checkpoint loaded: {self.total_crawled} items already crawled")
                    return True
            except Exception as e:
                logger.error(f"Error loading checkpoint: {e}")
        return False
    
    async def save_results(self, filename: str = None):
        """Save results to JSONL file"""
        if not filename:
            filename = f"{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        
        output_file = self.output_dir / filename
        async with aiofiles.open(output_file, 'ab') as f:
            for item in self.results:
                await f.write(orjson.dumps(item) + b'\n')
        
        count = len(self.results)
        self.results.clear()
        logger.info(f"Saved {count} items to {output_file}")
    
    @abstractmethod
    async def get_urls_to_crawl(self) -> List[str]:
        """Get list of URLs to crawl. Override in subclass."""
        pass
    
    @abstractmethod
    async def parse_page(self, url: str, html: str) -> Optional[Dict[str, Any]]:
        """Parse HTML and extract data. Override in subclass."""
        pass
    
    async def crawl_url(self, url: str, pbar: tqdm) -> Optional[Dict[str, Any]]:
        """Crawl a single URL"""
        if url in self.crawled_urls:
            pbar.update(1)
            return None
        
        html = await self.fetch(url)
        if html:
            result = await self.parse_page(url, html)
            if result:
                self.crawled_urls.add(url)
                self.total_crawled += 1
                self.results.append(result)
                
                # Save checkpoint periodically
                if self.total_crawled % self.checkpoint_interval == 0:
                    await self.save_checkpoint()
                    await self.save_results()
                
                pbar.update(1)
                return result
        else:
            self.failed_urls.append(url)
        
        pbar.update(1)
        return None
    
    async def run(self, limit: Optional[int] = None, resume: bool = True):
        """Main crawl loop"""
        logger.info(f"Starting {self.name} crawler...")
        start_time = time.time()
        
        await self.init_session()
        
        if resume:
            await self.load_checkpoint()
        
        try:
            urls = await self.get_urls_to_crawl()
            
            if limit:
                urls = urls[:limit]
            
            # Filter out already crawled URLs
            urls = [u for u in urls if u not in self.crawled_urls]
            
            logger.info(f"URLs to crawl: {len(urls)}")
            
            with tqdm(total=len(urls), desc=self.name) as pbar:
                tasks = [self.crawl_url(url, pbar) for url in urls]
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # Final save
            await self.save_results()
            await self.save_checkpoint()
            
            elapsed = time.time() - start_time
            logger.info(f"Crawl completed: {self.total_crawled} items in {elapsed:.2f}s")
            logger.info(f"Failed URLs: {len(self.failed_urls)}")
            
        finally:
            await self.close_session()
        
        return self.total_crawled
