import json

# PRODUCTION: Full data
INPUT_FILE = "data/merged_raw_3_sources.jsonl"
OUTPUT_FILE = "data/01_deduplicated.jsonl"

def normalize_key(text):
    return text.strip().lower() if text else ""

def run():
    print("Step 1: Deduplicating (Tax + Name + Address)...")
    seen_keys = set()
    count_in = 0
    count_out = 0
    duplicates = 0
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f_in, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            if not line.strip(): continue
            count_in += 1
            try:
                item = json.loads(line)
                
                key = (
                    normalize_key(item.get('tax_code')),
                    normalize_key(item.get('company_name')),
                    normalize_key(item.get('address'))
                )
                
                if key in seen_keys:
                    duplicates += 1
                    continue
                
                seen_keys.add(key)
                f_out.write(json.dumps(item, ensure_ascii=False) + '\n')
                count_out += 1
                
                if count_out % 100000 == 0:
                    print(f"Processed {count_out}...", end='\r')
            except: continue
            
    print(f"\nDONE Step 1.")
    print(f"Input: {count_in} | Output: {count_out} | Duplicates: {duplicates}")
    print(f"Output: {OUTPUT_FILE}")

if __name__ == "__main__":
    run()
