"""
Simple URL File Crawler
SEG301 - Milestone 1

Crawl từ danh sách URLs đã tạo sẵn (seeds).
Phương pháp này ổn định hơn vì không cần crawl listing pages.
"""

import asyncio
import aiohttp
import aiofiles
import orjson
import re
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Set
from datetime import datetime
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential

from .parser import DataParser

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('file_crawler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FileCrawler:
    """
    Crawler that reads URLs from a text file.
    Each URL is one company detail page.
    """
    
    def __init__(
        self,
        urls_file: str,
        output_dir: str = "data",
        max_concurrent: int = 10,
        rate_limit: float = 1.0,
        checkpoint_interval: int = 50
    ):
        self.urls_file = Path(urls_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_concurrent = max_concurrent
        self.rate_limit = rate_limit
        self.checkpoint_interval = checkpoint_interval
        
        self.ua = UserAgent()
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.session: Optional[aiohttp.ClientSession] = None
        self.parser = DataParser(use_segmentation=True)
        
        # Progress tracking
        self.crawled_urls: Set[str] = set()
        self.failed_urls: List[str] = []
        self.results: List[Dict[str, Any]] = []
        self.total_crawled = 0
        
        # File paths
        name = self.urls_file.stem
        self.checkpoint_file = self.output_dir / f"{name}_checkpoint.json"
        self.output_file = self.output_dir / f"{name}_output.jsonl"
    
    def get_headers(self) -> Dict[str, str]:
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'vi-VN,vi;q=0.9',
        }
    
    async def init_session(self):
        if self.session is None:
            connector = aiohttp.TCPConnector(
                limit=self.max_concurrent,
                limit_per_host=5
            )
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=30)
            )
    
    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=30))
    async def fetch(self, url: str) -> Optional[str]:
        async with self.semaphore:
            await asyncio.sleep(self.rate_limit)
            
            try:
                async with self.session.get(url, headers=self.get_headers()) as resp:
                    if resp.status == 200:
                        return await resp.text()
                    elif resp.status == 429:
                        logger.warning(f"Rate limited, waiting 30s...")
                        await asyncio.sleep(30)
                        raise Exception("Rate limited")
                    elif resp.status == 404:
                        return None  # Company doesn't exist
                    else:
                        logger.warning(f"HTTP {resp.status} for {url}")
                        return None
            except asyncio.TimeoutError:
                logger.error(f"Timeout: {url}")
                raise
            except Exception as e:
                logger.error(f"Error: {url} - {e}")
                raise
    
    async def parse_masothue(self, url: str, html: str) -> Optional[Dict[str, Any]]:
        """Parse masothue.com company page"""
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Extract tax code from URL
            match = re.search(r'/(\d{10,13})', url)
            tax_code = match.group(1) if match else None
            
            if not tax_code:
                return None
            
            # Company name from h1
            name_elem = soup.select_one('h1')
            company_name = name_elem.get_text(strip=True) if name_elem else ""
            company_name = re.sub(r'^\d{10,13}\s*[-–]\s*', '', company_name)
            
            if not company_name or 'không tồn tại' in company_name.lower():
                return None
            
            data = {
                'id': f"mst_{tax_code}",
                'source': 'masothue',
                'url': url,
                'tax_code': tax_code,
                'company_name': company_name,
                'company_name_segmented': self.parser.segment_text(company_name),
                'address': '',
                'representative': '',
                'phone': '',
                'industry': '',
                'registration_date': '',
                'status': '',
                'crawled_at': datetime.now().isoformat()
            }
            
            # Parse table.table-taxinfo
            table = soup.select_one('table.table-taxinfo')
            if table:
                rows = table.select('tr')
                for row in rows:
                    cells = row.select('td')
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        value = cells[-1].get_text(strip=True)
                        
                        if 'địa chỉ' in label:
                            data['address'] = value
                        elif 'đại diện' in label:
                            data['representative'] = value
                        elif 'điện thoại' in label:
                            data['phone'] = value
                        elif 'ngành nghề' in label:
                            data['industry'] = value
                        elif 'ngày' in label and ('hoạt động' in label or 'cấp' in label):
                            data['registration_date'] = value
                        elif 'tình trạng' in label or 'trạng thái' in label:
                            data['status'] = value
            
            if data['address']:
                data['address_segmented'] = self.parser.segment_text(data['address'])
            
            return data
            
        except Exception as e:
            logger.error(f"Parse error {url}: {e}")
            return None
    
    async def save_checkpoint(self):
        checkpoint = {
            'crawled_urls': list(self.crawled_urls),
            'failed_urls': self.failed_urls,
            'total_crawled': self.total_crawled
        }
        async with aiofiles.open(self.checkpoint_file, 'wb') as f:
            await f.write(orjson.dumps(checkpoint))
    
    async def load_checkpoint(self):
        if self.checkpoint_file.exists():
            try:
                async with aiofiles.open(self.checkpoint_file, 'rb') as f:
                    data = orjson.loads(await f.read())
                    self.crawled_urls = set(data.get('crawled_urls', []))
                    self.failed_urls = data.get('failed_urls', [])
                    self.total_crawled = data.get('total_crawled', 0)
                    logger.info(f"Loaded checkpoint: {self.total_crawled} already crawled")
            except Exception as e:
                logger.error(f"Error loading checkpoint: {e}")
    
    async def save_results(self):
        if not self.results:
            return
        
        async with aiofiles.open(self.output_file, 'ab') as f:
            for item in self.results:
                await f.write(orjson.dumps(item) + b'\n')
        
        logger.info(f"Saved {len(self.results)} items")
        self.results.clear()
    
    async def crawl_url(self, url: str, pbar) -> Optional[Dict[str, Any]]:
        if url in self.crawled_urls:
            pbar.update(1)
            return None
        
        html = await self.fetch(url)
        if html:
            result = await self.parse_masothue(url, html)
            if result:
                self.crawled_urls.add(url)
                self.total_crawled += 1
                self.results.append(result)
                
                if self.total_crawled % self.checkpoint_interval == 0:
                    await self.save_checkpoint()
                    await self.save_results()
                
                pbar.update(1)
                pbar.set_postfix({'saved': self.total_crawled})
                return result
        else:
            self.failed_urls.append(url)
        
        pbar.update(1)
        return None
    
    async def run(self, limit: int = None, resume: bool = True):
        logger.info(f"Starting FileCrawler...")
        logger.info(f"Input: {self.urls_file}")
        logger.info(f"Output: {self.output_file}")
        
        await self.init_session()
        
        if resume:
            await self.load_checkpoint()
        
        # Load URLs from file
        with open(self.urls_file, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip()]
        
        # Filter already crawled
        urls = [u for u in urls if u not in self.crawled_urls]
        
        if limit:
            urls = urls[:limit]
        
        logger.info(f"URLs to crawl: {len(urls)}")
        
        try:
            with tqdm(total=len(urls), desc="Crawling") as pbar:
                # Process in batches to manage memory
                batch_size = 100
                for i in range(0, len(urls), batch_size):
                    batch = urls[i:i+batch_size]
                    tasks = [self.crawl_url(url, pbar) for url in batch]
                    await asyncio.gather(*tasks, return_exceptions=True)
            
            await self.save_results()
            await self.save_checkpoint()
            
            logger.info(f"Done! Total crawled: {self.total_crawled}")
            logger.info(f"Failed: {len(self.failed_urls)}")
            
        finally:
            await self.close_session()
        
        return self.total_crawled


async def crawl_from_file(
    urls_file: str,
    output_dir: str = "data",
    limit: int = None,
    resume: bool = True
):
    """Convenience function"""
    crawler = FileCrawler(
        urls_file=urls_file,
        output_dir=output_dir,
        max_concurrent=10,
        rate_limit=1.0
    )
    return await crawler.run(limit=limit, resume=resume)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python file_crawler.py <urls_file> [limit]")
        sys.exit(1)
    
    urls_file = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    asyncio.run(crawl_from_file(urls_file, limit=limit))
