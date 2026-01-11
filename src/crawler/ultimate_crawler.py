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

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
DATA_DIR = Path("data_member1")
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

# --- ENGINE ---
class UltimateCrawler:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        # REGISTER ALL SOURCES HERE
        self.sources = [
            MasothueSource(), 
            HosocongtySource(),
            TimCongTySource()
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

    def run(self):
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
        
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(15) # Force timeout faster
        
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
                    links = source.parse_listing(driver.page_source)
                    
                    if not links:
                        print(f"  [?] No links found on {source.name}. Maybe structure changed?")
                        source.mark_blocked(60)
                        continue
                        
                    print(f"  Found {len(links)} links. Processing...")
                    
                    # 4. Process Details
                    new_items = 0
                    for link in links:
                        if link in self.visited_urls:
                            continue
                        
                        driver.get(link)
                        time.sleep(1) # Polite delay
                        
                        detail_data = source.parse_detail(driver.page_source, link)
                        if detail_data:
                            # Standardize Data
                            detail_data['crawled_at'] = datetime.now().isoformat()
                            self.save_data(detail_data)
                            self.visited_urls.add(link)
                            new_items += 1
                        else:
                            print(f"  [-] Failed to parse detail: {link}")
                    
                    if new_items > 0:
                        self.save_checkpoint()
                        source.reset_status()
                    
                    # Next page
                    page_cursor += 1
                    # Avoid predictable patterns
                    time.sleep(random.uniform(2, 5))

                except Exception as e:
                    print(f"  [Error] {e}")
                    source.mark_blocked(60)
                    
        finally:
            driver.quit()

if __name__ == "__main__":
    UltimateCrawler().run()
