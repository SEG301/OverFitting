"""
ULTIMATE CRAWLER (THE HYDRA)
Chiến thuật: Multi-Source Failover.
Tự động xoay vòng giữa Masothue, Hosocongty, ThongtinDN để đảm bảo 100% Uptime.
"""

import time
import json
import random
import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

import asyncio
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
DATA_DIR = Path("data_member3")
OUTPUT_FILE = DATA_DIR / "final_dataset.jsonl"
CHECKPOINT_FILE = DATA_DIR / "checkpoint_hydra.json"

class BaseSource:
    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.cooldown_until = 0
        self.consecutive_errors = 0

    def is_ready(self) -> bool:
        return time.time() > self.cooldown_until

    def mark_blocked(self, duration=300):
        self.cooldown_until = time.time() + duration
        self.consecutive_errors += 1
        print(f"  [!] {self.name} BLOCKED/ERROR. Cooldown for {duration}s. (Errors: {self.consecutive_errors})")

    def reset_status(self):
        self.consecutive_errors = 0

    def get_listing_url(self, page: int) -> str:
        raise NotImplementedError

    def parse_listing(self, html: str) -> List[str]:
        raise NotImplementedError

    def parse_detail(self, html: str, url: str) -> Optional[Dict]:
        raise NotImplementedError

# --- SOURCE: MASOTHUE.COM ---
class MasothueSource(BaseSource):
    def __init__(self):
        super().__init__("Masothue", "https://masothue.com/tra-cuu-ma-so-thue-doanh-nghiep-moi-thanh-lap")

    def get_listing_url(self, page: int) -> str:
        return f"{self.base_url}?page={page}"

    def parse_listing(self, html: str) -> List[str]:
        soup = BeautifulSoup(html, 'lxml')
        links = []
        for a in soup.select('div.tax-listing h3 a'):
            href = a.get('href')
            if href: links.append(f"https://masothue.com{href}")
        return links

    def parse_detail(self, html: str, url: str) -> Optional[Dict]:
        soup = BeautifulSoup(html, 'lxml')
        h1 = soup.select_one('h1')
        if not h1: return None
        
        data = {
            'source': self.name, 'url': url,
            'company_name': h1.get_text(strip=True),
            'tax_code': '', 'address': ''
        }
        
        table = soup.select_one('table.table-taxinfo')
        if table:
            for row in table.select('tr'):
                text = row.get_text(strip=True)
                if 'Mã số thuế' in text:
                    cols = row.select('td')
                    if len(cols)>1: data['tax_code'] = cols[1].get_text(strip=True)
                elif 'Địa chỉ' in text:
                    cols = row.select('td')
                    if len(cols)>1: data['address'] = cols[1].get_text(strip=True)
        
        return data if data['tax_code'] else None

# --- SOURCE: HOSOCONGTY.VN ---
class HosocongtySource(BaseSource):
    def __init__(self):
        super().__init__("Hosocongty", "https://hosocongty.vn/ha-noi-tp1")

    def get_listing_url(self, page: int) -> str:
        return f"{self.base_url}/page-{page}"

    def parse_listing(self, html: str) -> List[str]:
        soup = BeautifulSoup(html, 'lxml')
        links = []
        for h3 in soup.select('ul.hsdn li h3 a'):
            links.append(h3.get('href'))
        return links

    def parse_detail(self, html: str, url: str) -> Optional[Dict]:
        soup = BeautifulSoup(html, 'lxml')
        h1 = soup.select_one('h1')
        if not h1: return None
        
        data = {
            'source': self.name, 'url': url,
            'company_name': h1.get_text(strip=True),
            'tax_code': '', 'address': ''
        }
        
        for li in soup.select('ul.info li'):
            text = li.get_text(strip=True)
            if 'Mã số thuế:' in text:
                data['tax_code'] = text.replace('Mã số thuế:', '').strip()
            elif 'Địa chỉ:' in text:
                data['address'] = text.replace('Địa chỉ:', '').strip()
                
                
        return data if data['tax_code'] else None

# --- SOURCE: TIMCONGTY.COM ---
class TimCongTySource(BaseSource):
    def __init__(self):
        super().__init__("TimCongTy", "https://timcongty.com")
        # Base urls: https://timcongty.com/thanh-pho-ha-noi/
        
    def get_listing_url(self, page: int) -> str:
        # Focusing on Hanoi/HCM for density
        region = "thanh-pho-ha-noi" if page % 2 == 0 else "thanh-pho-ho-chi-minh"
        return f"{self.base_url}/{region}/?page={page}"

    def parse_listing(self, html: str) -> List[str]:
        soup = BeautifulSoup(html, 'lxml')
        links = []
        # Selector assumption: h3 a or similar
        for a in soup.select('div.content-left div.item h3 a'):
             links.append(a.get('href'))
        return links

    def parse_detail(self, html: str, url: str) -> Optional[Dict]:
        soup = BeautifulSoup(html, 'lxml')
        h1 = soup.select_one('h1')
        if not h1: return None
        
        data = {
            'source': self.name, 'url': url,
            'company_name': h1.get_text(strip=True),
            'tax_code': '', 'address': ''
        }
        
        # Info extraction
        # Usually in div.info
        txt = soup.get_text()
        # Regex is safer here
        mst = re.search(r'Mã số thuế: (\d+)', txt)
        if mst: data['tax_code'] = mst.group(1)
        
        addr = re.search(r'Địa chỉ: (.*)', txt)
        # Cleaner extraction in TimCongTy usually involves checking p tags or table
        if not data['address']:
             # try meta
             pass

        return data if data['tax_code'] else None

# --- SOURCE: REVIEWCONGTY.COM ---
class ReviewCongTySource(BaseSource):
    def __init__(self):
        super().__init__("ReviewCongTy", "https://reviewcongty.com")

    def get_listing_url(self, page: int) -> str:
        return f"{self.base_url}/companies?page={page}"

    def parse_listing(self, html: str) -> List[str]:
        soup = BeautifulSoup(html, 'lxml')
        links = []
        for a in soup.select('a[href^="/companies/"]'):
            href = a.get('href')
            if href:
                full_url = f"https://reviewcongty.com{href}" if not href.startswith('http') else href
                links.append(full_url)
        return links

    def parse_detail(self, html: str, url: str) -> Optional[Dict]:
        soup = BeautifulSoup(html, 'lxml')
        h1 = soup.select_one('h1.company-info__name') or soup.select_one('h1')
        if not h1: return None
        
        data = {
            'source': self.name, 'url': url,
            'company_name': h1.get_text(strip=True),
            'tax_code': '', 'address': ''
        }
        return data


# --- SOURCE: TRATENCONGTY.COM (FAST MODE) ---
from curl_cffi.requests import AsyncSession

class FastTraTenCongTySource(BaseSource):
    def __init__(self):
        super().__init__("TraTenCongTy", "https://www.tratencongty.com")
        self.cookies = self.load_cookies()
        self.ua = self.load_ua()
        self.session = None

    def load_cookies(self):
        try:
            with open("cookies.json", 'r') as f:
                cookies_list = json.load(f)
                # Convert list of dicts to simple dict for curl_cffi if needed, 
                # but curl_cffi AsyncSession accepts browser-style cookies often or dict.
                # Let's clean them.
                c = {}
                for cookie in cookies_list:
                    c[cookie['name']] = cookie['value']
                return c
        except: return {}

    def load_ua(self):
        try:
            with open("user_agent.txt", 'r') as f:
                return f.read().strip()
        except: 
            return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    async def get_page_content(self, url: str) -> Optional[str]:
        if not self.session:
            self.session = AsyncSession(
                impersonate="chrome110",
                cookies=self.cookies,
                headers={"User-Agent": self.ua},
                timeout=30
            )
        try:
            r = await self.session.get(url)
            if r.status_code == 200:
                return r.text
            elif r.status_code == 403 or r.status_code == 429:
                print(f"  [!] FastFetch Blocked ({r.status_code}). Switching to Slow Mode might be needed.")
                return None
        except Exception as e:
            print(f"  [!] FastFetch Error: {e}")
        return None

    def get_listing_url(self, page: int) -> str:
        return f"{self.base_url}/?page={page}"

    def parse_listing(self, html: str) -> List[str]:
        soup = BeautifulSoup(html, 'lxml')
        links = []
        for div in soup.select('div.search-results'):
            a = div.select_one('a')
            if a:
                href = a.get('href')
                if href and '/company/' in href:
                    links.append(href)
        return links

    def parse_detail(self, html: str, url: str) -> Optional[Dict]:
        soup = BeautifulSoup(html, 'lxml')
        
        # Name
        h1 = soup.select_one('h1')
        name = h1.get_text(strip=True) if h1 else ""
        if not name:
            title = soup.select_one('title')
            if title: name = title.get_text(strip=True)
            
        if not name: return None

        data = {
            'source': self.name, 'url': url,
            'company_name': name,
            'tax_code': '', 'address': ''
        }
        
        text = soup.get_text(separator=' ')
        addr_match = re.search(r'Địa chỉ:\s*(.*?)(?:$|\n|Qt:|- Đại diện)', text)
        if addr_match:
            data['address'] = addr_match.group(1).strip()
            
        rep_match = re.search(r'Đại diện pháp luật:\s*(.*?)(?:$|\n|<)', text)
        if rep_match:
            data['legal_representative'] = rep_match.group(1).strip()

        slug_match = re.search(r'company/([a-f0-9-]+)', url)
        if slug_match:
             mst_match = re.search(r'Mã số thuế:.*?(\d{10,13})', text)
             if mst_match:
                 data['tax_code'] = mst_match.group(1)
             else:
                 data['tax_code'] = "REF-" + slug_match.group(1).split('-')[0]
        
        return data

# --- SOURCE: MASOTHUE.COM (FAST MODE) ---
class FastMasothueSource(BaseSource):
    def __init__(self):
        super().__init__("Masothue", "https://masothue.com/tra-cuu-ma-so-thue-doanh-nghiep-moi-thanh-lap")
        self.cookies = self.load_cookies()
        self.ua = self.load_ua()
        self.session = None

    def load_cookies(self):
        try:
            with open("cookies.json", 'r') as f:
                cookies_list = json.load(f)
                c = {}
                for cookie in cookies_list:
                    c[cookie['name']] = cookie['value']
                return c
        except: return {}

    def load_ua(self):
        try:
            with open("user_agent.txt", 'r') as f:
                return f.read().strip()
        except: 
            return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    async def get_page_content(self, url: str) -> Optional[str]:
        if not self.session:
            self.session = AsyncSession(
                impersonate="chrome110",
                cookies=self.cookies,
                headers={"User-Agent": self.ua},
                timeout=30
            )
        try:
            r = await self.session.get(url)
            if r.status_code == 200:
                return r.text
            elif r.status_code == 403 or r.status_code == 429:
                print(f"  [!] FastMasothue Blocked ({r.status_code}).")
                return None
        except Exception as e:
            print(f"  [!] FastMasothue Error: {e}")
        return None

    def get_listing_url(self, page: int) -> str:
        return f"{self.base_url}?page={page}"

    def parse_listing(self, html: str) -> List[str]:
        soup = BeautifulSoup(html, 'lxml')
        links = []
        for a in soup.select('div.tax-listing h3 a'):
            href = a.get('href')
            if href: links.append(f"https://masothue.com{href}")
        return links

    def parse_detail(self, html: str, url: str) -> Optional[Dict]:
        soup = BeautifulSoup(html, 'lxml')
        h1 = soup.select_one('h1')
        if not h1: return None
        
        data = {
            'source': self.name, 'url': url,
            'company_name': h1.get_text(strip=True),
            'tax_code': '', 'address': ''
        }
        
        table = soup.select_one('table.table-taxinfo')
        if table:
            for row in table.select('tr'):
                text = row.get_text(strip=True)
                if 'Mã số thuế' in text:
                    cols = row.select('td')
                    if len(cols)>1: data['tax_code'] = cols[1].get_text(strip=True)
                elif 'Địa chỉ' in text:
                    cols = row.select('td')
                    if len(cols)>1: data['address'] = cols[1].get_text(strip=True)
        
        return data if data['tax_code'] else None

# --- ENGINE ---
class UltimateCrawler:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.sources = [
            # FastTraTenCongTySource(),
            FastMasothueSource()
        ]
        self.visited_urls = self.load_checkpoint()
        self.saved_count = len(self.visited_urls)

    def load_checkpoint(self) -> set:
        if CHECKPOINT_FILE.exists():
            try:
                with open(CHECKPOINT_FILE, 'r') as f:
                    return set(json.load(f))
            except: pass
        return set()

    def save_checkpoint(self):
        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump(list(self.visited_urls), f)

    def save_data(self, data: Dict):
        with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
        self.saved_count += 1
        print(f"    [+] Saved #{self.saved_count}: {data['company_name'][:40]}... ({data['source']})")

    async def run(self):
        print(">>> INITIALIZING HYDRA ENGINE (Optimized Speed)...")
        options = uc.ChromeOptions()
        # options.add_argument('--headless=new') 
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--disable-popup-blocking')
        
        # PERFORMANCE OPTIMIZATIONS
        options.page_load_strategy = 'eager' # Don't wait for full load
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')
        options.add_argument('--blink-settings=imagesEnabled=false') # Block Images
        
        # Block heavy resources via prefs
        prefs = {
            "profile.managed_default_content_settings.images": 2, # Block Images
            "profile.default_content_setting_values.notifications": 2,
            "profile.managed_default_content_settings.stylesheets": 2, # Block CSS
            # "profile.managed_default_content_settings.javascript": 2, # Keep JS for Cloudflare
            "profile.managed_default_content_settings.cookies": 1,
            "profile.managed_default_content_settings.plugins": 1,
            "profile.managed_default_content_settings.popups": 2,
            "profile.managed_default_content_settings.geolocation": 2,
            "profile.managed_default_content_settings.media_stream": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        # Browser Path Detection for macOS
        import os
        browser_path = None
        possible_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                browser_path = path
                print(f"  [+] Found browser: {path}")
                break
        
        if not browser_path:
            print("  [!] No compatible browser (Chrome/Brave/Edge) found!")
            return

        options.binary_location = browser_path
        
        try:
            # Try with explicit version for Brave (detected as 141 in logs)
            # and browser executable path
            driver = uc.Chrome(options=options, browser_executable_path=browser_path, version_main=141)
        except Exception as e:
            print(f"  [Init Failed] {e}. Retrying with fresh options...")
            
            # Re-create options to avoid RuntimeError: you cannot reuse the ChromeOptions object
            options = uc.ChromeOptions()
            options.add_argument('--ignore-certificate-errors')
            options.add_argument('--disable-popup-blocking')
            options.page_load_strategy = 'eager'
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-gpu')
            options.add_argument('--blink-settings=imagesEnabled=false')
            options.add_experimental_option("prefs", prefs)
            options.binary_location = browser_path
            
            # Fallback retry without specific version or just standard init
            driver = uc.Chrome(options=options, browser_executable_path=browser_path)
        
        driver.set_page_load_timeout(30) # Force timeout faster
        
        try:
            page_cursor = 1
            
            while True:
                # 1. Select Best Available Source
                active_sources = [s for s in self.sources if s.is_ready()]
                if not active_sources:
                    print("  [!] All sources blocked. Sleeping 60s...")
                    time.sleep(60)
                    continue
                
                # Pick one (Round Robin or Random)
                source = random.choice(active_sources)
                print(f"\n[TARGET]: {source.name} | Page {page_cursor}")
                
                try:
                    # 2. Fetch Listing
                    driver.get(source.get_listing_url(page_cursor))
                    
                    # Anti-Bot Check
                    if "Just a moment" in driver.title or "Page4Kids" in driver.title:
                        source.mark_blocked(300) # Block 5 mins
                        continue

                    # Wait for content
                    time.sleep(3) 
                    
                    # 3. Parse Listing
                    # HYBRID: Check if source supports fast fetch first (Cookies)
                    html = None
                    if hasattr(source, 'get_page_content'):
                        # FAST MODE
                        html = await source.get_page_content(source.get_listing_url(page_cursor))
                        
                    if not html:
                        # SLOW/FALLBACK: Browser Mode
                        driver.get(source.get_listing_url(page_cursor))
                        
                        # Anti-Bot Check
                        if "Just a moment" in driver.title or "Page4Kids" in driver.title:
                            source.mark_blocked(300) # Block 5 mins
                            continue

                        # Wait for content
                        time.sleep(2)  
                        html = driver.page_source

                    links = source.parse_listing(html)
                    
                    if not links:
                        print(f"  [?] No links found on {source.name}. Maybe structure changed?")
                        source.mark_blocked(60)
                        continue
                        
                    print(f"  Found {len(links)} links. Processing concurrently...")
                    
                    # 4. Process Details PARALLEL
                    async def process_link(link):
                        if link in self.visited_urls: return None
                        
                        try:
                            # Fetch
                            detail_html = None
                            if hasattr(source, 'get_page_content'):
                                detail_html = await source.get_page_content(link)
                            
                            # Fallback if fast fetch failed or not available (and we have driver)
                            if not detail_html and driver:
                                driver.get(link)
                                # time.sleep(0.5) 
                                detail_html = driver.page_source
                            elif not detail_html:
                                return None

                            # Parse
                            detail_data = source.parse_detail(detail_html, link)
                            if detail_data:
                                detail_data['crawled_at'] = datetime.now().isoformat()
                                return detail_data
                        except Exception as e:
                            # print(f"    Error processing {link}: {e}")
                            pass
                        return None

                    # Run batch
                    # Limit concurrency per batch to avoid total DoS self
                    batch_results = await asyncio.gather(*[process_link(l) for l in links])
                    
                    new_items = 0
                    for res in batch_results:
                        if res:
                            self.save_data(res)
                            self.visited_urls.add(res['url'])
                            new_items += 1
                    
                    if new_items > 0:
                        self.save_checkpoint()
                        source.reset_status()
                    
                    # Next page
                    page_cursor += 1
                    # Reduced delay for Turbo Mode
                    if not hasattr(source, 'get_page_content'):
                        time.sleep(1)
                    else:
                        await asyncio.sleep(0.5) # Slight breathing room for CPU/Net

                except Exception as e:
                    print(f"  [Error] {e}")
                    source.mark_blocked(60)
                    
        finally:
            driver.quit()

if __name__ == "__main__":
    asyncio.run(UltimateCrawler().run())
