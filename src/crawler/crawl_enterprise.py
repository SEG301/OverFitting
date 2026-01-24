import requests
import concurrent.futures
import json
import time
import threading
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json
import time
import threading
import concurrent.futures
from pathlib import Path
from unidecode import unidecode
from src.crawler.parser import parse_company_list, parse_company_detail, is_empty_page

# --- CONFIG ---
BASE_URL = "https://infodoanhnghiep.com"
REGIONS = [
    "Ha-Noi", "TP-Ho-Chi-Minh", "Da-Nang", "Hai-Phong", "Can-Tho",
    "Bac-Ninh", "Hai-Duong", "Hung-Yen", "Vinh-Phuc", "Quang-Ninh", "Thai-Binh", "Nam-Dinh", "Ninh-Binh", "Ha-Nam", "Phu-Tho", "Bac-Giang", "Thai-Nguyen", "Lang-Son", "Tuyen-Quang", "Yen-Bai", "Lao-Cai", "Ha-Giang", "Cao-Bang", "Bac-Kan", "Dien-Bien", "Lai-Chau", "Son-La", "Hoa-Binh",
    "Thanh-Hoa", "Nghe-An", "Ha-Tinh", "Quang-Binh", "Quang-Tri", "Thua-Thien-Hue", "Quang-Nam", "Quang-Ngai", "Binh-Dinh", "Phu-Yen", "Khanh-Hoa", "Ninh-Thuan", "Binh-Thuan", "Kon-Tum", "Gia-Lai", "Dak-Lak", "Dak-Nong", "Lam-Dong",
    "Binh-Phuoc", "Tay-Ninh", "Binh-Duong", "Dong-Nai", "Ba-Ria-Vung-Tau", "Long-An", "Tien-Giang", "Ben-Tre", "Tra-Vinh", "Vinh-Long", "Dong-Thap", "An-Giang", "Kien-Giang", "Hau-Giang", "Soc-Trang", "Bac-Lieu", "Ca-Mau"
]
WORKERS = 100 # Increased for ultimate speed
DEEP_CRAWL = True 
MAX_DOCS = 1000000
OUTPUT_FILE = Path("data/enterprise_data.jsonl")

# --- GLOBAL SESSION & POOLS ---
SESSION = requests.Session()
# Maximize connection pool to 1000
adapter = HTTPAdapter(pool_connections=200, pool_maxsize=1000, max_retries=Retry(total=3, backoff_factor=0.5))
SESSION.mount("https://", adapter)
SESSION.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

# Global executor for sub-tasks to avoid overhead
DETAIL_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=500)

# --- GLOBAL STATE ---
SEEN_RECORDS = set() 
LOCK = threading.Lock()
TOTAL_UNIQUE = 0
STOP_FLAG = False

def fetch_single_detail(item):
    """Small worker for parallel detail fetching."""
    try:
        resp = SESSION.get(item['url'], timeout=10)
        if resp.status_code == 200:
            details = parse_company_detail(resp.text)
            item.update(details)
            return True
    except:
        pass
    return False

def crawling_job(region, page):
    """Fetches and parses a single page."""
    url = f"{BASE_URL}/{region}/trang-{page}/"
    
    try:
        resp = SESSION.get(url, timeout=15)
        if resp.status_code == 404: return "END_OF_PAGE"
        if resp.status_code != 200: return []
        if page > 1 and "trang-" not in resp.url: return "END_OF_PAGE"
        if is_empty_page(resp.text): return "END_OF_PAGE"

        raw_items = parse_company_list(resp.text, base_url=BASE_URL)
        
        unique_results = []
        for item in raw_items:
            key = (item['tax_code'], item['company_name'], item['address'])
            with LOCK:
                if key not in SEEN_RECORDS:
                    SEEN_RECORDS.add(key)
                    unique_results.append(item)
        
        if DEEP_CRAWL and unique_results:
            # Using GLOBAL executor for maximum thread reuse
            deep_success = 0
            futures = [DETAIL_EXECUTOR.submit(fetch_single_detail, it) for it in unique_results]
            for fut in concurrent.futures.as_completed(futures):
                if fut.result(): deep_success += 1
            
            if unique_results:
                unique_results[0]['_deep_batch'] = deep_success
                    
        return unique_results
    except:
        return []

def load_checkpoint():
    """Loads existing data and counts records per region to resume accurately."""
    global TOTAL_UNIQUE
    region_counts = {r: 0 for r in REGIONS}
    
    if OUTPUT_FILE.exists():
        print(f"Loading checkpoint from {OUTPUT_FILE} (analyzing progress)...")
        count = 0
        with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    d = json.loads(line)
                    # Create unique key
                    if 'tax_code' in d:
                        SEEN_RECORDS.add((d['tax_code'], d.get('company_name', ''), d.get('address', '')))
                        count += 1
                        
                        # Heuristic to detect region from crawl data so we can skip pages
                        
                        addr_str = unidecode(d.get('address', '')) # Normalize to ASCII for matching
                        url_str = unidecode(d.get('url', ''))
                        
                        # Simple check for the current region being processed
                        for reg in REGIONS:
                            region_keyword = reg.replace("-", " ") 
                            # region_keyword like 'Ha Noi' matches normalized '..., Ha Noi'
                            if region_keyword in addr_str or region_keyword in url_str:
                                region_counts[reg] += 1
                                break # Count for first match only
                                
                        if count % 100000 == 0:
                            print(f"Loaded {count} records...")
                except: pass
        TOTAL_UNIQUE = count
        print(f"Checkpoint loaded: {count} unique records.")
        return region_counts
    return region_counts

def start_spider():
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    region_counts = load_checkpoint()
    
    print(f"\n--- CORE SPIDER RESTORED (SMART RESUME) ---")
    print(f"Workers: {WORKERS} | Target Count: {MAX_DOCS}")
    
    global TOTAL_UNIQUE, STOP_FLAG
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
        for region in REGIONS:
            if STOP_FLAG: break
            
            # Smart Resume Calculation
            existing_count = region_counts.get(region, 0)
            # Estimate 20 records per page. 
            # We subtract a safety buffer of 50 pages (1000 records) to ensure no gaps
            start_page = max(1, (existing_count // 20) - 50) 
            
            print(f"\n--- SCANNING REGION: {region} ---")
            print(f"   Note: Found {existing_count} existing records. Resuming from page ~{start_page}")
            
            page = start_page
            while True:
                if STOP_FLAG: break
                batch_size = 50
                batch_end = page + batch_size
                print(f"[{region}] Fetching pages {page} to {batch_end-1}...", end='\r')
                
                futures = {executor.submit(crawling_job, region, p): p for p in range(page, batch_end)}
                
                batch_data = []
                stop_region = False
                
                for future in concurrent.futures.as_completed(futures):
                    res = future.result()
                    if res == "END_OF_PAGE":
                        stop_region = True
                    elif isinstance(res, list):
                        batch_data.extend(res)
                
                if batch_data:
                    # Filter duplicates AGAIN just in case of overlap
                    verified_new_items = []
                    for item in batch_data:
                        key = (item['tax_code'], item['company_name'], item['address'])
                        # If crawling_job added it to SEEN, it's fine. 
                        # But crawling_job checks SEEN too.
                        # We just need to counting logic here.
                        verified_new_items.append(item)

                    if verified_new_items:     
                        batch_new = len(verified_new_items)
                        batch_deep = sum(item.pop('_deep_batch', 0) for item in verified_new_items)
                        
                        with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
                            for item in verified_new_items:
                                f.write(json.dumps(item, ensure_ascii=False) + '\n')
                        
                        with LOCK:
                            TOTAL_UNIQUE += batch_new
                            print(f"[{region}] Pages {page}-{batch_end-1}: NEW {batch_new} | DEEP {batch_deep} | TOTAL {TOTAL_UNIQUE}/{MAX_DOCS}      ")
                            if TOTAL_UNIQUE >= MAX_DOCS:
                                print(f"\n!!! TARGET REACHED: {TOTAL_UNIQUE} records !!! Stopping crawler.")
                                STOP_FLAG = True
                                break
                    else:
                         print(f"[{region}] Pages {page}-{batch_end-1}: Overlap/Duplicate batch.      ", end='\r')

                else:
                    print(f"[{region}] Pages {page}-{batch_end-1}: No new records found.      ", end='\r')

                if stop_region or STOP_FLAG:
                    if stop_region: print(f"\nFinished Region: {region} (Reached last page)")
                    break
                    
                page += batch_size
                if page > 55000: break

    print(f"\nCrawler finished. Final count: {TOTAL_UNIQUE} records saved in {OUTPUT_FILE}")

if __name__ == "__main__":
    start_spider()
