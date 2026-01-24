import json
import os

# 3 file nguồn dữ liệu gốc
INPUT_FILES = [
    "data/3cities_data.jsonl",
    "data/crawled_new_63_provinces.jsonl",
    "data/milestone1_final_deep_1m.jsonl"
]

OUTPUT_FILE = "data/merged_raw_3_sources.jsonl"

def normalize_text(text):
    if not text: return ""
    return text.strip().lower()

def merge_files():
    print("Merging 3 data sources...")
    seen_keys = set()
    total_records = 0
    duplicates = 0
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        for file_path in INPUT_FILES:
            if not os.path.exists(file_path):
                print(f"Warning: File not found {file_path}")
                continue
                
            print(f"Processing {file_path}...")
            count = 0
            
            with open(file_path, 'r', encoding='utf-8') as f_in:
                for line in f_in:
                    line = line.strip()
                    if not line: continue
                    
                    try:
                        item = json.loads(line)
                        
                        # Composite key: Tax + Name + Address
                        tax = normalize_text(item.get('tax_code', ''))
                        name = normalize_text(item.get('company_name', ''))
                        addr = normalize_text(item.get('address', ''))
                        
                        unique_key = (tax, name, addr)
                        
                        if unique_key in seen_keys:
                            duplicates += 1
                            continue
                            
                        seen_keys.add(unique_key)
                        f_out.write(json.dumps(item, ensure_ascii=False) + '\n')
                        count += 1
                        total_records += 1
                        
                        if total_records % 100000 == 0:
                            print(f"  Merged {total_records} records...", end='\r')
                            
                    except json.JSONDecodeError:
                        continue
                        
            print(f"  -> {count} records from {os.path.basename(file_path)}")

    print(f"\n{'='*40}")
    print(f"DONE! Total unique records: {total_records}")
    print(f"Duplicates skipped: {duplicates}")
    print(f"Output: {OUTPUT_FILE}")

if __name__ == "__main__":
    merge_files()
