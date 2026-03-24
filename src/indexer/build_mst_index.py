import os
import time
import json
import pickle
import re

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
JSONL_PATH = os.path.join(PROJECT_ROOT, "data", "milestone1_fixed.jsonl")
INDEX_PATH = os.path.join(PROJECT_ROOT, "data", "index", "mst_index.pkl")

def build_mst_index():
    print(f"Building MST Index...")
    start_time = time.time()
    
    mst_dict = {}
    tax_regex = re.compile(br'"tax_code":\s*"([^"]+)"')
    
    with open(JSONL_PATH, "rb") as f:
        offset = 0
        count = 0
        while True:
            line = f.readline()
            if not line:
                break
                
            m = tax_regex.search(line)
            if m:
                tax_code = m.group(1).decode('utf-8')
                mst_dict[tax_code] = offset
                
            offset += len(line)
            count += 1
            
            if count % 500000 == 0:
                print(f"  Processed {count:,} documents...")
                
    print(f"Found {len(mst_dict):,} unique MSTs.")
    print("Saving to pickle...")
    
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    with open(INDEX_PATH, "wb") as f:
        pickle.dump(mst_dict, f)
        
    elapsed = time.time() - start_time
    print(f"Done in {elapsed:.2f}s!")
    print(f"Index size: {os.path.getsize(INDEX_PATH) / 1024 / 1024:.2f} MB")

if __name__ == "__main__":
    build_mst_index()
