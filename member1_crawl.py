"""
Optimized Crawl Strategy for Member 1 - Version 2
SEG301 - Milestone 1

Chiến lược: Crawl từ trang "Doanh nghiệp mới" và theo Tỉnh/Thành phố
với rate limit hợp lý để tránh bị block.
"""

import asyncio
import aiohttp
import aiofiles
import orjson
import re
import random
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm
from fake_useragent import UserAgent

# Lazy import parser
_parser = None
def get_parser():
    global _parser
    if _parser is None:
        from src.crawler.parser import DataParser
        _parser = DataParser(use_segmentation=True)
    return _parser


class OptimizedMasothueCrawler:
    """
    Crawler tối ưu cho masothue.com
    Crawl từ:
    1. Doanh nghiệp mới: https://masothue.com/tra-cuu-ma-so-thue-doanh-nghiep-moi-thanh-lap/?page=N
    2. Theo tỉnh: https://masothue.com/tra-cuu-ma-so-thue-theo-tinh/ha-noi-1?page=N
    """
    
    # URLs cho Member 1 (Hà Nội + Doanh nghiệp mới)
    SOURCES = [
        ("Hà Nội", "https://masothue.com/tra-cuu-ma-so-thue-theo-tinh/ha-noi-1"),
        ("DN Mới", "https://masothue.com/tra-cuu-ma-so-thue-doanh-nghiep-moi-thanh-lap"),
    ]
    
    BASE_URL = "https://masothue.com"
    
    def __init__(self, output_dir: str = "data_member1", max_pages_per_source: int = 5000):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_pages = max_pages_per_source
        self.ua = UserAgent()
        self.session = None
        
        # Progress
        self.crawled_urls = set()
        self.company_urls = []
        self.results = []
        self.total_crawled = 0
        self.total_failed = 0
        
        # Files
        self.output_file = self.output_dir / "masothue_member1.jsonl"
        self.checkpoint_file = self.output_dir / "checkpoint_member1.json"
        self.urls_file = self.output_dir / "company_urls.txt"
    
    def get_headers(self):
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml',
            'Accept-Language': 'vi-VN,vi;q=0.9',
        }
    
    async def init_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
    
    async def close_session(self):
        if self.session:
            await self.session.close()
    
    async def fetch(self, url: str, retries: int = 3) -> str:
        """Fetch với retry và rate limit cao"""
        for attempt in range(retries):
            try:
                await asyncio.sleep(random.uniform(2.5, 4))
                
                async with self.session.get(url, headers=self.get_headers()) as resp:
                    if resp.status == 200:
                        return await resp.text()
                    elif resp.status == 429:
                        wait = 30 * (attempt + 1)
                        print(f"\nRate limited. Waiting {wait}s...")
                        await asyncio.sleep(wait)
                    elif resp.status == 404:
                        return None
                    else:
                        await asyncio.sleep(10)
            except Exception as e:
                print(f"\nError: {e}")
                await asyncio.sleep(10)
        return None
    
    async def get_company_urls_from_listing(self, base_url: str, source_name: str, max_pages: int = 100) -> list:
        """Lấy danh sách URLs công ty từ trang listing"""
        urls = []
        page = 1
        
        print(f"\n[{source_name}] Getting company URLs...")
        
        while page <= max_pages:
            page_url = f"{base_url}?page={page}" if page > 1 else base_url
            html = await self.fetch(page_url)
            
            if not html:
                break
            
            soup = BeautifulSoup(html, 'lxml')
            
            # Tìm links công ty (bắt đầu bằng /MST)
            found = 0
            for link in soup.select('a[href^="/"]'):
                href = link.get('href', '')
                if re.match(r'^/\d{10,13}', href):
                    full_url = f"{self.BASE_URL}{href}"
                    if full_url not in urls and full_url not in self.crawled_urls:
                        urls.append(full_url)
                        found += 1
            
            if found == 0:
                break
            
            print(f"\r[{source_name}] Page {page}: Found {len(urls)} companies", end="")
            page += 1
        
        print()
        return urls
    
    async def parse_company(self, url: str, html: str) -> dict:
        """Parse thông tin công ty"""
        soup = BeautifulSoup(html, 'lxml')
        parser = get_parser()
        
        # Tax code from URL
        match = re.search(r'/(\d{10,13})', url)
        tax_code = match.group(1) if match else None
        if not tax_code:
            return None
        
        # Company name
        h1 = soup.select_one('h1')
        company_name = h1.get_text(strip=True) if h1 else ""
        company_name = re.sub(r'^\d{10,13}\s*[-–]\s*', '', company_name)
        
        if not company_name or 'không tồn tại' in company_name.lower():
            return None
        
        data = {
            'id': f"mst_{tax_code}",
            'source': 'masothue',
            'url': url,
            'tax_code': tax_code,
            'company_name': company_name,
            'company_name_segmented': parser.segment_text(company_name),
            'address': '',
            'representative': '',
            'industry': '',
            'registration_date': '',
            'status': '',
            'crawled_at': datetime.now().isoformat()
        }
        
        # Parse table
        table = soup.select_one('table.table-taxinfo')
        if table:
            for row in table.select('tr'):
                cells = row.select('td')
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[-1].get_text(strip=True)
                    
                    if 'địa chỉ' in label:
                        data['address'] = value
                        data['address_segmented'] = parser.segment_text(value)
                    elif 'đại diện' in label:
                        data['representative'] = value
                    elif 'ngành nghề' in label:
                        data['industry'] = value
                    elif 'ngày' in label:
                        data['registration_date'] = value
                    elif 'tình trạng' in label or 'trạng thái' in label:
                        data['status'] = value
        
        return data
    
    async def save_checkpoint(self):
        data = {
            'crawled_urls': list(self.crawled_urls),
            'total_crawled': self.total_crawled,
            'total_failed': self.total_failed
        }
        async with aiofiles.open(self.checkpoint_file, 'wb') as f:
            await f.write(orjson.dumps(data))
    
    async def load_checkpoint(self):
        if self.checkpoint_file.exists():
            try:
                async with aiofiles.open(self.checkpoint_file, 'rb') as f:
                    data = orjson.loads(await f.read())
                    self.crawled_urls = set(data.get('crawled_urls', []))
                    self.total_crawled = data.get('total_crawled', 0)
                    self.total_failed = data.get('total_failed', 0)
                    print(f"Loaded checkpoint: {self.total_crawled} already crawled")
            except:
                pass
    
    async def save_results(self):
        if not self.results:
            return
        async with aiofiles.open(self.output_file, 'ab') as f:
            for item in self.results:
                await f.write(orjson.dumps(item) + b'\n')
        self.results.clear()
    
    async def crawl_company(self, url: str) -> bool:
        if url in self.crawled_urls:
            return True
        
        html = await self.fetch(url)
        if html:
            data = await self.parse_company(url, html)
            if data:
                self.results.append(data)
                self.crawled_urls.add(url)
                self.total_crawled += 1
                
                if self.total_crawled % 50 == 0:
                    await self.save_results()
                    await self.save_checkpoint()
                
                return True
        
        self.total_failed += 1
        return False
    
    async def run(self, limit: int = None, resume: bool = True, collect_urls_only: bool = False):
        """
        Chạy crawler
        
        Args:
            limit: Giới hạn số lượng
            resume: Tiếp tục từ checkpoint
            collect_urls_only: Chỉ thu thập URLs, không crawl chi tiết
        """
        print("=" * 60)
        print("MEMBER 1 - Masothue Crawler (Optimized)")
        print("=" * 60)
        
        await self.init_session()
        
        if resume:
            await self.load_checkpoint()
        
        # Phase 1: Thu thập URLs từ các nguồn
        print("\n📋 Phase 1: Collecting company URLs...")
        
        for source_name, base_url in self.SOURCES:
            urls = await self.get_company_urls_from_listing(
                base_url, 
                source_name, 
                max_pages=self.max_pages
            )
            self.company_urls.extend(urls)
        
        # Loại bỏ duplicates
        self.company_urls = list(set(self.company_urls))
        
        # Lưu URLs
        with open(self.urls_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self.company_urls))
        
        print(f"\n✅ Total unique URLs: {len(self.company_urls)}")
        print(f"   Saved to: {self.urls_file}")
        
        if collect_urls_only:
            await self.close_session()
            return
        
        # Phase 2: Crawl chi tiết từng công ty
        print("\n📥 Phase 2: Crawling company details...")
        
        # Filter đã crawl
        urls_to_crawl = [u for u in self.company_urls if u not in self.crawled_urls]
        
        if limit:
            urls_to_crawl = urls_to_crawl[:limit]
        
        print(f"URLs to crawl: {len(urls_to_crawl)}")
        print("-" * 60)
        
        try:
            for url in tqdm(urls_to_crawl, desc="Crawling"):
                await self.crawl_company(url)
            
            await self.save_results()
            await self.save_checkpoint()
            
        except KeyboardInterrupt:
            print("\n\n⚠️ Interrupted! Saving progress...")
            await self.save_results()
            await self.save_checkpoint()
        
        finally:
            await self.close_session()
        
        print("\n" + "=" * 60)
        print(f"✅ DONE!")
        print(f"   Total crawled: {self.total_crawled}")
        print(f"   Failed: {self.total_failed}")
        print(f"   Output: {self.output_file}")
        print("=" * 60)


async def main():
    import sys
    
    limit = None
    collect_only = False
    
    for arg in sys.argv[1:]:
        if arg == "--urls-only":
            collect_only = True
        elif arg.isdigit():
            limit = int(arg)
    
    crawler = OptimizedMasothueCrawler(max_pages_per_source=100)
    await crawler.run(limit=limit, collect_urls_only=collect_only)


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║  SEG301 - Milestone 1: Data Acquisition                 ║
║  Member 1 Crawler - Masothue.com                        ║
╚══════════════════════════════════════════════════════════╝

Usage:
  python member1_crawl.py              # Crawl full
  python member1_crawl.py 100          # Crawl 100 companies
  python member1_crawl.py --urls-only  # Only collect URLs
    """)
    asyncio.run(main())
