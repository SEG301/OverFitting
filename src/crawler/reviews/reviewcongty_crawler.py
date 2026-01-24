import asyncio
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession
from ..base_crawler import AsyncCrawler

class ReviewcongtyCrawler(AsyncCrawler):
    def __init__(self, output_dir: str, max_concurrent: int = 20, rate_limit: float = 0.1):
        super().__init__("Reviewcongty", output_dir, max_concurrent, rate_limit)
        self.base_url = "https://reviewcongty.com"
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
        urls = []
        # Try crawling /companies listing
        # page=1, 2, 3
        
        detail_urls = set()
        
        async def fetch_listing(page):
            url = f"{self.base_url}/companies?page={page}"
            html = await self.fetch(url)
            if html:
                soup = BeautifulSoup(html, 'lxml')
                # Look for company links
                # Typically a.company-link or h2 a
                # We'll select all links that look like /companies/slug
                for a in soup.select('a[href^="/companies/"]'):
                    href = a.get('href')
                    if href:
                        full_url = f"{self.base_url}{href}"
                        detail_urls.add(full_url)

        # Limit to 5 pages
        tasks = [fetch_listing(i) for i in range(1, 6)]
        await asyncio.gather(*tasks)
        
        print(f"Found {len(detail_urls)} companies on ReviewCongTy.")
        return list(detail_urls)

    async def parse_page(self, url: str, html: str) -> Optional[Dict[str, Any]]:
        soup = BeautifulSoup(html, 'lxml')
        h1 = soup.select_one('h1.company-info__name') # Guessing class
        if not h1:
             h1 = soup.select_one('h1') # Fallback
            
        if not h1: return None
        
        data = {
            'source': self.name,
            'url': url,
            'company_name': h1.get_text(strip=True),
            'reviews': []
        }
        
        # Parse reviews?
        # Assuming .review-item
        reviews = []
        for review in soup.select('.review-content'):
            reviews.append(review.get_text(strip=True))
        
        data['reviews'] = reviews
        data['has_reviews'] = len(reviews) > 0
        
        return data
