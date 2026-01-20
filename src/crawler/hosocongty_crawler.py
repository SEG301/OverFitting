import asyncio
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession
from .base_crawler import AsyncCrawler

class HosocongyCrawler(AsyncCrawler):
    def __init__(self, output_dir: str, max_concurrent: int = 20, rate_limit: float = 0.1):
        super().__init__("Hosocongty", output_dir, max_concurrent, rate_limit)
        self.base_url = "https://hosocongty.vn"
        self.curl_session: Optional[AsyncSession] = None

    async def init_session(self):
        """Initialize curl-cffi session"""
        if self.curl_session is None:
            self.curl_session = AsyncSession(
                impersonate="chrome110",
                headers=self.get_headers(),
                timeout=30
            )

    async def close_session(self):
        """Close curl-cffi session"""
        if self.curl_session:
            await self.curl_session.close()
            self.curl_session = None

    async def fetch(self, url: str) -> Optional[str]:
        """Fetch URL using curl-cffi"""
        async with self.semaphore:
            await asyncio.sleep(self.rate_limit)
            try:
                response = await self.curl_session.get(url)
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 429:
                    print(f"Rate limited on {url}, waiting...")
                    await asyncio.sleep(10)
                    return None
                else:
                    print(f"HTTP {response.status_code} for {url}")
                    return None
            except Exception as e:
                print(f"Error fetching {url}: {e}")
                return None

    async def get_urls_to_crawl(self) -> List[str]:
        # Generate listing URLs for major cities to crawl
        # We will crawl the first 50 pages of Hanoi and HCM
        urls = []
        regions = ['ha-noi-tp1', 'ho-chi-minh-tp2']
        
        # We fetch listings to get company URLs
        # But AsyncCrawler structure usually expects a list of detail URLs or handles the crawling flow.
        # Since AsyncCrawler.run() expects a list of URLs to crawl directly,
        # we might need to change strategy: "get_urls_to_crawl" should return detail URLs.
        # However, getting all detail URLs first is expensive.
        # For this task, we will return LISTING URLs and handle parsing them in parse_page?
        # No, base_crawler logic is: for url in urls: fetch -> parse -> save.
        
        # If we return listing URLs, parse_page would return a list of links? BaseCrawler expects a Dict result.
        
        # We need a 2-step process: 
        # 1. Crawl Listings -> Get Detail URLs
        # 2. Crawl Details -> Get Data
        
        # Since I cannot easily change BaseCrawler, I will implement a generator here 
        # that fetches listings first (sequentially or parallel) then returns the list of detail URLs.
        
        print("Gathering seed URLs from listings...")
        detail_urls = set()
        
        async def fetch_listing(region, page):
            url = f"{self.base_url}/{region}/page-{page}"
            html = await self.fetch(url)
            if html:
                soup = BeautifulSoup(html, 'lxml')
                links = soup.select('ul.hsdn li h3 a')
                for a in links:
                    href = a.get('href')
                    if href:
                        detail_urls.add(href)

        # Limit to 5 pages for demo/start
        tasks = []
        for region in regions:
            for page in range(1, 6): # 5 pages per region
                tasks.append(fetch_listing(region, page))
        
        await asyncio.gather(*tasks)
        print(f"Found {len(detail_urls)} companies to crawl.")
        return list(detail_urls)

    async def parse_page(self, url: str, html: str) -> Optional[Dict[str, Any]]:
        soup = BeautifulSoup(html, 'lxml')
        h1 = soup.select_one('h1')
        if not h1:
            return None
        
        data = {
            'source': self.name,
            'url': url,
            'company_name': h1.get_text(strip=True),
            'tax_code': None,
            'address': None
        }
        
        # Extract based on structure found in UltimateCrawler
        # ul.info li
        for li in soup.select('ul.info li'):
            text = li.get_text(strip=True)
            if 'Mã số thuế:' in text:
                data['tax_code'] = text.replace('Mã số thuế:', '').strip()
            elif 'Địa chỉ:' in text:
                data['address'] = text.replace('Địa chỉ:', '').strip()
        
        return data if data['tax_code'] else None
