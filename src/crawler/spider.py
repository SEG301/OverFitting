import requests
import concurrent.futures
import json
import time
import threading
from pathlib import Path
from .parser import parse_company_list, is_empty_page

# --- CONFIG (FULL 63 PROVINCES RESTORED) ---
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
WORKERS = 50 
DEEP_CRAWL = True  # Set to True to visit detail pages for Representative, Phone, etc.
OUTPUT_FILE = Path("data/milestone1_final_full.jsonl")

# --- GLOBAL STATE (Thread-Safe Deduplication) ---
# Restoring original key (Tax, Name, Address)
SEEN_RECORDS = set() 
LOCK = threading.Lock()
TOTAL_UNIQUE = 0

def fetch_detail(item, session):
    """Worker function to fetch company details."""
    try:
        url = item['url']
        resp = session.get(url, timeout=10)
        if resp.status_code == 200:
            from .parser import parse_company_detail
            details = parse_company_detail(resp.text)
            item.update(details)
    except:
        pass
    return item

def crawling_job(region, page):
    """Fetches and parses a single page."""
    url = f"{BASE_URL}/{region}/trang-{page}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        session = requests.Session()
        resp = session.get(url, headers=headers, timeout=15)
        if resp.status_code == 404: 
            return "END_OF_PAGE"
        if resp.status_code != 200: 
            return []

        # Detect Redirect (Fix that user liked)
        if page > 1 and "trang-" not in resp.url:
            return "END_OF_PAGE"
            
        if is_empty_page(resp.text):
            return "END_OF_PAGE"

        # Content Parsing
        raw_items = parse_company_list(resp.text, base_url=BASE_URL)
        
        # Deduplication using Original Mechanism
        unique_results = []
        for item in raw_items:
            # Original Key: (tax, name, addr)
            key = (item['tax_code'], item['company_name'], item['address'])
            with LOCK:
                if key not in SEEN_RECORDS:
                    SEEN_RECORDS.add(key)
                    unique_results.append(item)
        
        if DEEP_CRAWL and unique_results:
            # Fetch details in parallel for this batch
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as detail_executor:
                detail_executor.map(lambda x: fetch_detail(x, session), unique_results)
                    
        return unique_results

    except Exception as e:
        return []

def load_checkpoint():
    """Loads existing data to resume crawling without duplicates."""
    global TOTAL_UNIQUE
    if OUTPUT_FILE.exists():
        print(f"Loading checkpoint from {OUTPUT_FILE}...")
        count = 0
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    d = json.loads(line)
                    if 'tax_code' in d:
                        # Restore original key mapping
                        SEEN_RECORDS.add((d['tax_code'], d.get('company_name', ''), d.get('address', '')))
                        count += 1
                except: pass
        TOTAL_UNIQUE = count
        print(f"Checkpoint loaded: {count} unique records.")

def start_spider():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    load_checkpoint()
    
    print(f"\n--- CORE SPIDER RESTORED (63 PROVINCES) ---")
    print(f"Workers: {WORKERS} | Target Regions: 63")
    
    global TOTAL_UNIQUE
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
        for region in REGIONS:
            print(f"\nScanning Region: {region}")
            page = 1
            while True:
                # Restoring original Batch Size of 50
                batch_size = 50
                futures = {executor.submit(crawling_job, region, p): p for p in range(page, page + batch_size)}
                
                batch_data = []
                stop_region = False
                
                for future in concurrent.futures.as_completed(futures):
                    res = future.result()
                    if res == "END_OF_PAGE":
                        stop_region = True
                    elif isinstance(res, list):
                        batch_data.extend(res)
                
                # Write results
                if batch_data:
                    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
                        for item in batch_data:
                            f.write(json.dumps(item, ensure_ascii=False) + '\n')
                    
                    with LOCK:
                        TOTAL_UNIQUE += len(batch_data)
                        print(f"Progress [{region}]: Total {TOTAL_UNIQUE} unique documents found.")

                if stop_region:
                    print(f"Region {region} finished (End of Pagination detected).")
                    break
                    
                page += batch_size
                if page > 50000: break

if __name__ == "__main__":
    start_spider()
