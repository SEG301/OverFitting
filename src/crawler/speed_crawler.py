import requests
from bs4 import BeautifulSoup
import concurrent.futures
import json
import time
from pathlib import Path
import random
import re
from datetime import datetime

# --- CONFIG ---
# --- CONFIG ---
BASE_URL = "https://infodoanhnghiep.com"
REGIONS = [
    # Top Cities
    "Ha-Noi", "TP-Ho-Chi-Minh", "Da-Nang", "Hai-Phong", "Can-Tho",
    # North
    "Bac-Ninh", "Hai-Duong", "Hung-Yen", "Vinh-Phuc", "Quang-Ninh", "Thai-Binh", "Nam-Dinh", "Ninh-Binh", "Ha-Nam", "Phu-Tho", "Bac-Giang", "Thai-Nguyen", "Lang-Son", "Tuyen-Quang", "Yen-Bai", "Lao-Cai", "Ha-Giang", "Cao-Bang", "Bac-Kan", "Dien-Bien", "Lai-Chau", "Son-La", "Hoa-Binh",
    # Central
    "Thanh-Hoa", "Nghe-An", "Ha-Tinh", "Quang-Binh", "Quang-Tri", "Thua-Thien-Hue", "Quang-Nam", "Quang-Ngai", "Binh-Dinh", "Phu-Yen", "Khanh-Hoa", "Ninh-Thuan", "Binh-Thuan", "Kon-Tum", "Gia-Lai", "Dak-Lak", "Dak-Nong", "Lam-Dong",
    # South
    "Binh-Phuoc", "Tay-Ninh", "Binh-Duong", "Dong-Nai", "Ba-Ria-Vung-Tau", "Long-An", "Tien-Giang", "Ben-Tre", "Tra-Vinh", "Vinh-Long", "Dong-Thap", "An-Giang", "Kien-Giang", "Hau-Giang", "Soc-Trang", "Bac-Lieu", "Ca-Mau"
]
MAX_PAGES = 5000 # Adjusted for Full Sweep (Rural areas have fewer pages)
WORKERS = 30 
OUTPUT_FILE = Path("data_member1/speed_data_v2.jsonl") # New file to avoid mess

# --- UTILS ---
def clean_text(text):
    return re.sub(r'\s+', ' ', text).strip()

def crawling_job(region, page):
    url = f"{BASE_URL}/{region}/trang-{page}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    results = []
    try:
        # Retry with backoff
        for attempt in range(3):
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200: break
                if resp.status_code == 404: return [] # End of pagination
                time.sleep(1 + attempt)
            except: time.sleep(1)
            
        if resp.status_code != 200: return []

        soup = BeautifulSoup(resp.text, 'lxml')
        
        # Structure CONFIRMED: div.company-item -> h3.company-name a
        items = soup.select('div.company-item') 

        for div in items:
            h3 = div.select_one('h3.company-name a')
            if not h3: continue
            
            link = h3.get('href')
            name = h3.get_text(strip=True)
            text = div.get_text(separator=' ', strip=True)
            
            # Simple extraction
            item = {
                'company_name': name,
                'tax_code': '',
                'address': '',
                'source': 'InfoDoanhNghiep',
                'url': link if link.startswith('http') else (BASE_URL + link) if link.startswith('/') else link, 
                'crawled_at': datetime.now().isoformat()
            }
            
            # MST
            mst_match = re.search(r'Mã số thuế:\s*(\d+)', text)
            if mst_match: item['tax_code'] = mst_match.group(1)
            
            # Address
            addr_match = re.search(r'Địa chỉ:\s*(.*?)(?:$|Mã số thuế|Đại diện)', text)
            if addr_match:
                 item['address'] = clean_text(addr_match.group(1))
            elif "Địa chỉ:" in text:
                 item['address'] = text.split("Địa chỉ:")[-1].strip()

            if item['tax_code']:
                results.append(item)
                
        return results

    except: return []

def run_speed_crawler():
    output_path = OUTPUT_FILE
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f">>> SPEED CRAWLER ACTIVATED (Target: {BASE_URL})")
    print(f">>> WORKERS: {WORKERS}")
    
    total_collected = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
        for region in REGIONS:
            print(f"\n--- REGION: {region} ---")
            
            # Dispatch batches tasks
            # Reduce batch size for instant feedback
            batch_size = 50
            for start_page in range(1, MAX_PAGES, batch_size):
                futures = {}
                end_page = min(start_page + batch_size, MAX_PAGES)
                
                print(f"Dispatching pages {start_page} to {end_page}...")
                
                for page in range(start_page, end_page):
                    futures[executor.submit(crawling_job, region, page)] = page
                
                # Collect
                items_in_batch = 0
                for future in concurrent.futures.as_completed(futures):
                    page_num = futures[future]
                    try:
                        data = future.result()
                        if data:
                            items_in_batch += len(data)
                            print(f"[Page {page_num}] Found {len(data)} items") # Realtime Feedback
                            
                            # Write immediately
                            with open(output_path, 'a', encoding='utf-8') as f:
                                for d in data:
                                    f.write(json.dumps(d, ensure_ascii=False) + '\n')
                                
                    except Exception as e:
                        pass
                
                total_collected += items_in_batch
                print(f"Batch Done. New: {items_in_batch}. Total: {total_collected}")
                
                if items_in_batch == 0 and start_page > 1:
                    print(f"Region {region} seems finished or blocked.")
                    break
                    
if __name__ == "__main__":
    run_speed_crawler()
