"""
FAST CRAWLER - SEG301 Milestone 1
Sử dụng curl_cffi để bypass JA3/TLS Fingerprinting.
Tốc độ cao gấp 10-20 lần so với requests/aiohttp thường.
"""

import asyncio
import json
import random
import re
from pathlib import Path
from datetime import datetime
from typing import List, Set, Dict

from curl_cffi.requests import AsyncSession
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from bs4 import BeautifulSoup

# Setup
console = Console()

class FastCrawler:
    def __init__(self, output_dir: str = "data_member1"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.output_file = self.output_dir / "masothue_fast.jsonl"
        self.checkpoint_file = self.output_dir / "checkpoint_fast.json"
        
        self.crawled_urls: Set[str] = set()
        self.urls_to_crawl: List[str] = []
        
        # Load parser lazily
        from src.crawler.parser import DataParser
        self.parser = DataParser(use_segmentation=True)

    async def load_checkpoint(self):
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.crawled_urls = set(data.get('crawled_urls', []))
                console.print(f"[green]Loaded checkpoint: {len(self.crawled_urls)} urls crawled[/green]")
            except Exception as e:
                console.print(f"[red]Error loading checkpoint: {e}[/red]")

    async def save_checkpoint(self):
        data = {'crawled_urls': list(self.crawled_urls)}
        with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(data, f)
            
    async def save_result(self, data: Dict):
        with open(self.output_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')

    async def fetch(self, session: AsyncSession, url: str) -> str:
        try:
            # Impersonate Chrome 110 to bypass WAF
            response = await session.get(url, impersonate="chrome110", timeout=20)
            if response.status_code == 200:
                return response.text
            elif response.status_code == 429:
                return "RATE_LIMIT"
            else:
                return None
        except Exception as e:
            return None

    def parse(self, url: str, html: str) -> Dict:
        try:
            soup = BeautifulSoup(html, 'lxml')
            
            # Extract Tax Code
            tax_match = re.search(r'/(\d{10,13})', url)
            tax_code = tax_match.group(1) if tax_match else None
            if not tax_code: return None

            # Name
            h1 = soup.select_one('h1')
            name = h1.get_text(strip=True) if h1 else ""
            name = re.sub(r'^\d{10,13}\s*[-–]\s*', '', name)
            if not name or 'không tồn tại' in name.lower(): return None

            data = {
                'id': f"mst_{tax_code}",
                'source': 'masothue',
                'url': url,
                'tax_code': tax_code,
                'company_name': name,
                'company_name_segmented': self.parser.segment_text(name),
                'address': '',
                'industry': '',
                'registration_date': '',
                'crawled_at': datetime.now().isoformat()
            }

            # Table info
            table = soup.select_one('table.table-taxinfo')
            if table:
                for row in table.select('tr'):
                    cells = row.select('td')
                    if len(cells) >= 2:
                        label = cells[0].get_text(strip=True).lower()
                        val = cells[-1].get_text(strip=True)
                        
                        if 'địa chỉ' in label:
                            data['address'] = val
                        elif 'ngành nghề' in label:
                            data['industry'] = val
                        elif 'ngày' in label:
                            data['registration_date'] = val
            
            if data['address']:
                data['address_segmented'] = self.parser.segment_text(data['address'])
                
            return data
        except:
            return None

    async def get_listing_urls(self, session: AsyncSession, base_url: str, max_pages: int = 50) -> List[str]:
        urls = []
        for page in range(1, max_pages + 1):
            url = f"{base_url}?page={page}" if page > 1 else base_url
            html = await self.fetch(session, url)
            
            if not html or html == "RATE_LIMIT":
                break
                
            soup = BeautifulSoup(html, 'lxml')
            found = 0
            for a in soup.select('a[href^="/"]'):
                href = a.get('href', '')
                if re.match(r'^/\d{10,13}', href):
                    full = f"https://masothue.com{href}"
                    urls.append(full)
                    found += 1
            
            console.print(f"Scanned Listing Page {page}: Found {found} companies")
            if found == 0: break
            await asyncio.sleep(0.5) # Fast delay for listings
            
        return list(set(urls))

    async def run(self, limit: int = 1000):
        await self.load_checkpoint()
        
        async with AsyncSession() as session:
            # 1. Get Seeds (Listing Pages)
            console.print("[yellow]Phase 1: Fetching Seed URLs...[/yellow]")
            sources = [
                "https://masothue.com/tra-cuu-ma-so-thue-doanh-nghiep-moi-thanh-lap",
                "https://masothue.com/tra-cuu-ma-so-thue-theo-tinh/ha-noi-1"
            ]
            
            for source in sources:
                new_urls = await self.get_listing_urls(session, source, max_pages=50) # Scan 50 pages each
                self.urls_to_crawl.extend(new_urls)
            
            # Dedup and Filter
            self.urls_to_crawl = list(set(self.urls_to_crawl))
            self.urls_to_crawl = [u for u in self.urls_to_crawl if u not in self.crawled_urls]
            
            console.print(f"[bold cyan]Queue size: {len(self.urls_to_crawl)} companies[/bold cyan]")
            
            # 2. Crawl Details
            console.print("[yellow]Phase 2: Crawling Details with High Speed...[/yellow]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeRemainingColumn(),
                console=console
            ) as progress:
                
                task = progress.add_task("[green]Crawling...", total=len(self.urls_to_crawl))
                
                # Manual limiter: process chunks
                chunk_size = 5 # Concurrency
                
                for i in range(0, len(self.urls_to_crawl), chunk_size):
                    chunk = self.urls_to_crawl[i:i+chunk_size]
                    
                    tasks = []
                    for url in chunk:
                        tasks.append(self.fetch(session, url))
                    
                    results = await asyncio.gather(*tasks)
                    
                    for idx, html in enumerate(results):
                        url = chunk[idx]
                        if html and html != "RATE_LIMIT":
                            data = self.parse(url, html)
                            if data:
                                await self.save_result(data)
                                self.crawled_urls.add(url)
                                progress.advance(task)
                        elif html == "RATE_LIMIT":
                            console.print("[red]Rate Limit Hit! Cooling down 5s...[/red]")
                            await asyncio.sleep(5)

                    if i % 100 == 0 and i > 0:
                        await self.save_checkpoint()
                        
                    # Small delay between chunks to be nice, but much faster than before
                    await asyncio.sleep(0.5)

        await self.save_checkpoint()
        console.print("[bold green]DONE![/bold green]")

if __name__ == "__main__":
    import sys
    try:
        limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10000
        asyncio.run(FastCrawler().run(limit))
    except KeyboardInterrupt:
        pass
