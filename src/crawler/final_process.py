import json
from pathlib import Path
import re
import unicodedata
try:
    from pyvi import ViTokenizer
except ImportError:
    print("Please install pyvi: pip install pyvi")
    sys.exit(1)

# Input Files
SEARCH_FILES = [
    Path("data_member1/speed_data.jsonl"),
    Path("data_member1/speed_data_v2.jsonl")
]
OUTPUT_FILE = Path("data/milestone1_final.jsonl")

def normalize_text(text):
    if not text: return ""
    text = unicodedata.normalize('NFC', text)
    return re.sub(r'\s+', ' ', text).strip()

def process_and_merge():
    print(">>> STARTING FINAL DATA PROCESSING (DEDUPE + SEGMENTATION + INSIGHT)...")
    
    seen_ids = set()
    total_raw = 0
    total_clean = 0
    
    # Statistics
    total_tokens = 0
    vocab = set()
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as fout:
        for fpath in SEARCH_FILES:
            if not fpath.exists(): continue
            
            print(f"Reading {fpath}...")
            with open(fpath, 'r', encoding='utf-8') as fin:
                for line in fin:
                    total_raw += 1
                    line = line.strip()
                    if not line: continue
                    
                    try:
                        record = json.loads(line)
                        tax = record.get('tax_code', '').strip()
                        
                        if not tax or len(tax) < 9: continue 
                        
                        name = normalize_text(record.get('company_name', ''))
                        
                        # Dedupe Key
                        dedupe_key = (tax, name)
                        if dedupe_key in seen_ids: continue
                        seen_ids.add(dedupe_key)
                        
                        # Clean fields
                        record['company_name'] = name
                        record['address'] = normalize_text(record.get('address', ''))
                        
                        # Word Segmentation
                        name_seg = ViTokenizer.tokenize(name)
                        address_seg = ViTokenizer.tokenize(record['address'])
                        
                        record['company_name_seg'] = name_seg
                        record['address_seg'] = address_seg
                        
                        # Update Stats
                        tokens = name_seg.split() + address_seg.split()
                        total_tokens += len(tokens)
                        vocab.update(tokens)
                        
                        # Write
                        fout.write(json.dumps(record, ensure_ascii=False) + '\n')
                        total_clean += 1
                        
                        if total_clean % 50000 == 0:
                            print(f"Processed {total_clean} records...")
                            
                    except: pass
    
    print("-" * 30)
    print(">>> PROCESSING COMPLETED!")
    print(f"Total Raw Records: {total_raw}")
    print(f"Total Unique Records (Final): {total_clean}")
    
    # Insight Report
    print("\n>>> INSIGHT REPORT (1 Point Requirement):")
    if total_clean > 0:
        avg_len = total_tokens / total_clean
        print(f"1. Total Vocabulary Size: {len(vocab)} unique words")
        print(f"2. Average Document Length: {avg_len:.2f} words")
    else:
        print("No data to report.")

    if total_clean >= 1000000:
        print("\n✅ TARGET 1 MILLION REACHED!")
    else:
        print(f"\n⚠️ WARNING: REACHED {total_clean} RECORDS.")

if __name__ == "__main__":
    process_and_merge()
