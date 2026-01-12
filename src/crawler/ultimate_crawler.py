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
            'tax_code': '',
            'address': '',
            'representative': '',
            'params': {}, # Extra info
            'crawled_at': datetime.now().isoformat()
        }
        
        table = soup.select_one('table.table-taxinfo')
        if table:
            for row in table.select('tr'):
                cols = row.select('td')
                if len(cols) < 2: continue
                
                key = cols[0].get_text(strip=True).lower()
                val = cols[1].get_text(separator=' ', strip=True)
                
                if 'mã số thuế' in key:
                    data['tax_code'] = val
                elif 'địa chỉ' in key:
                    data['address'] = val
                elif 'đại diện pháp luật' in key:
                    data['representative'] = val
                elif 'ngày cấp' in key or 'ngày hoạt động' in key:
                    data['params']['date_active'] = val
                elif 'điện thoại' in key:
                    data['params']['phone'] = val
                elif 'quản lý bởi' in key:
                    data['params']['manager'] = val

        return data if data['tax_code'] else None

# --- SOURCE: TIMCONGTY.COM ---
class TimCongTySource(BaseSource):
    def __init__(self):
        super().__init__("TimCongTy", "https://timcongty.com")
        
    def get_listing_url(self, page: int) -> str:
        # Format: https://timcongty.com/thanh-pho-ha-noi/?page=1
        region = "thanh-pho-ha-noi" if page % 2 == 0 else "thanh-pho-ho-chi-minh"
        return f"{self.base_url}/{region}/?page={page}"

    def parse_listing(self, html: str) -> List[any]:
        # Returns List[Dict] (Listing Mode) for MAX SPEED
        soup = BeautifulSoup(html, 'lxml')
        items = []
        
        # Structure Timcongty:
        # div.content-left div.item
        #   h3 a (Name, Url)
        #   div.info (Tax code, Address...)
        for div in soup.select('div.content-left div.item'):
            h3 = div.select_one('h3 a')
            if not h3: continue
            
            item = {
                'source': self.name,
                'url': h3.get('href'),
                'company_name': h3.get_text(strip=True),
                'tax_code': '', 'address': ''
            }
            
            info = div.select_one('div.info')
            if info:
                text = info.get_text(separator=' ', strip=True)
                # Regex MST
                mst = re.search(r'Mã số thuế: (\d+)', text)
                if mst: item['tax_code'] = mst.group(1)
                
                # Regex Address or split
                if "Địa chỉ:" in text:
                     addr_part = text.split("Địa chỉ:")[1]
                     # Timcongty often puts Date after address or nothing
                     item['address'] = addr_part.split('Ngày cấp:')[0].strip()

            if item['tax_code']:
                items.append(item)
                
        return items

    def parse_detail(self, html: str, url: str) -> Optional[Dict]:
        return None

# --- SOURCE: HOSOCONGTY.VN ---
class HosocongtySource(BaseSource):
    def __init__(self):
        super().__init__("Hosocongty", "https://hosocongty.vn")
        
    def get_listing_url(self, page: int) -> str:
        region = "ha-noi" if page % 2 == 0 else "tp-ho-chi-minh"
        return f"{self.base_url}/{region}/page-{page}"

    def parse_listing(self, html: str) -> List[any]:
        # Returns List[Dict] (Direct Data) instead of Urls
        soup = BeautifulSoup(html, 'lxml')
        items = []
        
        # Structure Hosocongty listing:
        # ul.hsdn li
        #   h3 a (Name, Url)
        #   div (Info: MST, Address...)
        for li in soup.select('ul.hsdn li'):
            h3 = li.select_one('h3 a')
            if not h3: continue
            
            item = {
                'source': self.name,
                'url': h3.get('href'),
                'company_name': h3.get_text(strip=True),
                'tax_code': '', 'address': ''
            }
            
            # Extract info from listing text
            text = li.get_text(separator=' ', strip=True)
            # Regex for Tax Code
            mst_match = re.search(r'Mã số thuế:\s*(\d+)', text)
            if mst_match: item['tax_code'] = mst_match.group(1)
            
            # Simple Address extraction (often after MST or specific label)
            # But regex is tricky. Let's try basic split if labeled
            # "Địa chỉ: ..."
            if "Địa chỉ:" in text:
                parts = text.split("Địa chỉ:")
                if len(parts) > 1:
                     # Take only until next label if any, or end of string
                     addr = parts[1].split('Đại diện pháp luật:')[0].strip()
                     item['address'] = addr

            if item['tax_code']:
                items.append(item)
                
        return items

    def parse_detail(self, html: str, url: str) -> Optional[Dict]:
        return None # Not used in Listing mode

# --- ENGINE ---
# --- ENGINE (MULTI-THREADED MASOTHUE ONLY) ---
import concurrent.futures
import multiprocessing

class CrawlerWorker:
    def __init__(self, source: BaseSource, shared_visited: set, worker_id: int, total_workers: int):
        self.source = source
        self.visited = shared_visited
        self.worker_id = worker_id
        self.total_workers = total_workers
        
    def log(self, msg):
        print(f"[Worker {self.worker_id}] {msg}")

    def save_data(self, data: Dict):
        # Allow concurrent writes
        with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
        self.log(f"Saved: {data['company_name'][:30]}...")

    def run(self):
        # Create user data dir base
        base_profile = Path("data_browsers")
        base_profile.mkdir(parents=True, exist_ok=True)
        
        self.log(f"Starting Chrome (Profile: worker_{self.worker_id})...")
        options = uc.ChromeOptions()
        # options.add_argument('--headless=new') 
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--disable-popup-blocking')
        options.add_argument(f'--user-data-dir={base_profile.absolute()}/worker_{self.worker_id}')
        
        options.page_load_strategy = 'eager'
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-gpu')
        options.add_argument('--blink-settings=imagesEnabled=false')
        
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.stylesheets": 2,
            "profile.managed_default_content_settings.cookies": 1,
            "profile.managed_default_content_settings.popups": 2,
        }
        options.add_experimental_option("prefs", prefs)
        
        driver = uc.Chrome(options=options)
        driver.set_page_load_timeout(30)
        
        try:
            # Stride Pattern
            page = self.worker_id
            
            while True:
                url = self.source.get_listing_url(page)
                self.log(f"Loading Page {page}...")
                
                try:
                    driver.get(url)
                    
                    if "Just a moment" in driver.title or "Page4Kids" in driver.title:
                        self.log("Blocked. Sleep 60s...")
                        time.sleep(60)
                        continue
                        
                    time.sleep(3) # Wait Masothue
                    
                    links = self.source.parse_listing(driver.page_source)
                    
                    if not links:
                        self.log("No links found.")
                        if "404" in driver.title:
                            self.log("Hit end of data?")
                            break
                        page += self.total_workers
                        continue
                        
                    for link in links:
                        if link in self.visited: continue
                        try:
                            driver.get(link)
                            data = self.source.parse_detail(driver.page_source, link)
                            if data:
                                data['crawled_at'] = datetime.now().isoformat()
                                self.save_data(data)
                                self.visited.add(link)
                        except Exception as e: self.log(f"Detail err: {e}")
                    
                    page += self.total_workers
                    
                except Exception as e:
                    self.log(f"Page error: {e}")
                    time.sleep(5)
                    
        finally:
            driver.quit()

class UltimateCrawler:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        # STEALTH MODE: 1 WORKER ONLY
        self.source_template = MasothueSource() 
        self.visited_urls = self.load_checkpoint()
        self.num_workers = 1 

    def load_checkpoint(self) -> set:
        if CHECKPOINT_FILE.exists():
            try:
                with open(CHECKPOINT_FILE, 'r') as f:
                    return set(json.load(f))
            except: pass
        return set()

    def run(self):
        print(f">>> LAUNCHING STEALTH CRAWLER ({self.num_workers} Worker)...")
        print("Note: Running slowly to avoid ban.")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            futures = []
            for i in range(self.num_workers):
                # Start from Page 50 to avoid "Hot Zone"
                worker = CrawlerWorker(MasothueSource(), self.visited_urls, 50, self.num_workers)
                futures.append(executor.submit(worker.run))
            
            for future in concurrent.futures.as_completed(futures):
                try: future.result()
                except Exception as e: print(f"Worker died: {e}")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    UltimateCrawler().run()
