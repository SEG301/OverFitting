"""
Seed URL Generator
SEG301 - Milestone 1

Tạo sẵn danh sách URLs công ty để crawl,
hỗ trợ chia nhỏ cho team làm song song.
"""

import asyncio
import aiohttp
import re
import json
from pathlib import Path
from typing import List, Set
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm
from fake_useragent import UserAgent

ua = UserAgent()

async def fetch(session: aiohttp.ClientSession, url: str) -> str:
    """Fetch URL with rate limiting"""
    headers = {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'vi-VN,vi;q=0.9',
    }
    try:
        await asyncio.sleep(1.5)  # Rate limit
        async with session.get(url, headers=headers, timeout=30) as response:
            if response.status == 200:
                return await response.text()
            elif response.status == 429:
                print(f"Rate limited, waiting 30s...")
                await asyncio.sleep(30)
                return await fetch(session, url)
    except Exception as e:
        print(f"Error fetching {url}: {e}")
    return ""


async def get_masothue_industries(session: aiohttp.ClientSession) -> List[str]:
    """Lấy danh sách các ngành nghề từ masothue.com"""
    url = "https://masothue.com/tra-cuu-ma-so-thue-theo-nganh-nghe"
    html = await fetch(session, url)
    if not html:
        return []
    
    soup = BeautifulSoup(html, 'lxml')
    links = soup.select('a[href*="/tra-cuu-ma-so-thue-theo-nganh-nghe/"]')
    
    industries = []
    for link in links:
        href = link.get('href', '')
        if href and href != '/tra-cuu-ma-so-thue-theo-nganh-nghe':
            full_url = href if href.startswith('http') else f"https://masothue.com{href}"
            if full_url not in industries:
                industries.append(full_url)
    
    print(f"Found {len(industries)} industries on masothue.com")
    return industries


async def get_companies_from_industry(session: aiohttp.ClientSession, industry_url: str, max_pages: int = 100) -> Set[str]:
    """Lấy URLs công ty từ một ngành nghề"""
    urls = set()
    page = 1
    
    while page <= max_pages:
        page_url = f"{industry_url}?page={page}" if page > 1 else industry_url
        html = await fetch(session, page_url)
        
        if not html:
            break
        
        soup = BeautifulSoup(html, 'lxml')
        all_links = soup.select('a[href^="/"]')
        
        found = 0
        for link in all_links:
            href = link.get('href', '')
            if href and re.match(r'^/\d{10,13}-', href):
                urls.add(f"https://masothue.com{href}")
                found += 1
        
        if found == 0:
            break
        
        page += 1
    
    return urls


async def generate_seeds_masothue(output_file: str = "seeds_masothue.txt", industry_start: int = 1, industry_end: int = None):
    """Tạo file seed URLs từ masothue.com"""
    print("Generating seed URLs from masothue.com...")
    
    async with aiohttp.ClientSession() as session:
        # Lấy danh sách ngành
        industries = await get_masothue_industries(session)
        
        if industry_end:
            industries = industries[industry_start-1:industry_end]
        else:
            industries = industries[industry_start-1:]
        
        print(f"Processing {len(industries)} industries (from {industry_start})...")
        
        all_urls = set()
        for i, industry_url in enumerate(industries, 1):
            print(f"[{i}/{len(industries)}] {industry_url}")
            urls = await get_companies_from_industry(session, industry_url, max_pages=50)
            all_urls.update(urls)
            print(f"  -> Found {len(urls)} companies, Total: {len(all_urls)}")
            
            # Save progress every 5 industries
            if i % 5 == 0:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(sorted(all_urls)))
                print(f"  -> Saved progress: {len(all_urls)} URLs")
        
        # Final save
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sorted(all_urls)))
        
        print(f"\nDone! Saved {len(all_urls)} URLs to {output_file}")
        return all_urls


async def generate_seeds_from_taxcode_range(output_file: str = "seeds_from_taxcode.txt", start: int = 100000000, end: int = 100010000):
    """
    Tạo seed URLs bằng cách thử các mã số thuế trong range.
    Phương pháp này đảm bảo không bị block vì chỉ truy cập trang chi tiết.
    """
    print(f"Generating seed URLs from tax code range {start} to {end}...")
    
    urls = []
    for tax_code in range(start, end):
        # Mã số thuế 10 số
        urls.append(f"https://masothue.com/{tax_code:010d}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(urls))
    
    print(f"Generated {len(urls)} URLs to {output_file}")
    return urls


def split_seeds_for_team(input_file: str, num_members: int = 3):
    """Chia file seeds thành các phần cho team members"""
    with open(input_file, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    chunk_size = len(urls) // num_members
    
    for i in range(num_members):
        start = i * chunk_size
        end = start + chunk_size if i < num_members - 1 else len(urls)
        
        output_file = f"seeds_member{i+1}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(urls[start:end]))
        
        print(f"Member {i+1}: {end - start} URLs -> {output_file}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python seed_generator.py masothue [start] [end]  - Generate from masothue industries")
        print("  python seed_generator.py taxcode start end       - Generate from tax code range")
        print("  python seed_generator.py split input.txt 3       - Split seeds for 3 team members")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "masothue":
        start = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        end = int(sys.argv[3]) if len(sys.argv) > 3 else None
        asyncio.run(generate_seeds_masothue(industry_start=start, industry_end=end))
    
    elif command == "taxcode":
        start = int(sys.argv[2])
        end = int(sys.argv[3])
        asyncio.run(generate_seeds_from_taxcode_range(start=start, end=end))
    
    elif command == "split":
        input_file = sys.argv[2]
        num_members = int(sys.argv[3]) if len(sys.argv) > 3 else 3
        split_seeds_for_team(input_file, num_members)
    
    else:
        print(f"Unknown command: {command}")
