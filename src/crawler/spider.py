import requests
import concurrent.futures
import json
import time
import threading
from pathlib import Path
from .parser import parse_company_list, is_empty_page

# --- CONFIG ---
BASE_URL = "https://infodoanhnghiep.com"
REGIONS = [
    "Ha-Noi", "TP-Ho-Chi-Minh", "Da-Nang", "Hai-Phong", "Can-Tho",
    "Bac-Ninh", "Hai-Duong", "Hung-Yen", "Vinh-Phuc", "Quang-Ninh"
]
WORKERS = 50 
OUTPUT_FILE = Path("data/milestone1_final_full.jsonl")

# --- GLOBAL STATE (Thread-Safe Deduplication) ---
SEEN_RECORDS = set() # Store (tax_code) or (tax, name, addr)
LOCK = threading.Lock()
TOTAL_UNIQUE = 0

def crawling_job(region, page):
    """Fetches and parses a single page."""
    url = f"{BASE_URL}/{region}/trang-{page}/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 404: 
            return "END_OF_PAGE"
        if resp.status_code != 200: 
            return []

        # Detect Redirect (Server pushes back to Region Home if page overflow)
        if page > 1 and "trang-" not in resp.url:
            return "END_OF_PAGE"
            
        if is_empty_page(resp.text):
            return "END_OF_PAGE"

        # Parsing
        raw_items = parse_company_list(resp.text, base_url=BASE_URL)
        
        # Deduplication
        unique_results = []
        for item in raw_items:
            key = (item['tax_code'], item['company_name'])
            with LOCK:
                if key not in SEEN_RECORDS:
                    SEEN_RECORDS.add(key)
                    unique_results.append(item)
                    
        return unique_results

    except Exception as e:
        print(f"Error on {url}: {e}")
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
                        SEEN_RECORDS.add((d['tax_code'], d.get('company_name', '')))
                        count += 1
                except: pass
        TOTAL_UNIQUE = count
        print(f"Checkpoint loaded: {count} unique records.")

def start_spider():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    load_checkpoint()
    
    print(f"\n--- CORE SPIDER STARTING ---")
    print(f"Workers: {WORKERS} | Target Source: {BASE_URL}")
    
    global TOTAL_UNIQUE
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
        for region in REGIONS:
            print(f"\nScanning Region: {region}")
            page = 1
            while True:
                # Dispatch batch of 20 pages
                batch_size = 20
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
                    print(f"Finished Region: {region}")
                    break
                    
                page += batch_size
                if page > 50000: break

if __name__ == "__main__":
    start_spider()
