import json
from pathlib import Path
import re
import unicodedata

# Input Files
SEARCH_FILES = [
    Path("data_member1/speed_data.jsonl"),
    Path("data_member1/speed_data_v2.jsonl")
]
OUTPUT_FILE = Path("data/milestone1_final.jsonl")

def normalize_text(text):
    if not text: return ""
    # Normalize unicode (NFC)
    text = unicodedata.normalize('NFC', text)
    # Remove extra spaces
    return re.sub(r'\s+', ' ', text).strip()

def process_and_merge():
    print(">>> STARTING FINAL DATA PROCESSING...")
    
    seen_ids = set()
    total_raw = 0
    total_clean = 0
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as fout:
        for fpath in SEARCH_FILES:
            if not fpath.exists():
                print(f"Skipping {fpath} (Not found)")
                continue
            
            print(f"Reading {fpath}...")
            with open(fpath, 'r', encoding='utf-8') as fin:
                for line in fin:
                    total_raw += 1
                    line = line.strip()
                    if not line: continue
                    
                    try:
                        record = json.loads(line)
                        tax = record.get('tax_code', '').strip()
                        
                        # Basic Validation
                        if not tax or len(tax) < 9: continue 
                        
                        record['company_name'] = normalize_text(record.get('company_name', ''))
                        record['address'] = normalize_text(record.get('address', ''))
                        
                        # Composite Key Deduplication: Tax + Name
                        # This handles cases where Tax is same but Name differs slightly or changed
                        dedupe_key = (tax, record['company_name'])
                        
                        if dedupe_key in seen_ids:
                            continue
                        
                        seen_ids.add(dedupe_key)
                        
                        # Write
                        fout.write(json.dumps(record, ensure_ascii=False) + '\n')
                        total_clean += 1
                        
                        if total_clean % 100000 == 0:
                            print(f"Collected {total_clean} unique records...")
                            
                    except: pass
    
    print("-" * 30)
    print(">>> PROCESSING COMPLETED!")
    print(f"Total Raw Records: {total_raw}")
    print(f"Total Unique Records: {total_clean}")
    
    if total_clean >= 1000000:
        print("✅ SUCCESS: TARGET 1,000,000 REACHED!")
    else:
        print(f"⚠️ WARNING: STILL MISSING {1000000 - total_clean} RECORDS.")

if __name__ == "__main__":
    process_and_merge()
