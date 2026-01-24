import json

# PATHS
INPUT_FILE = "data/00_mapped_data.jsonl"
OUTPUT_FILE = "data/01_deduplicated.jsonl"

def normalize_key(text):
    return text.strip().lower() if text else ""

def run():
    print("Step 4: Deduplicating (Tax + Name + Address)...")
    seen_keys = set()
    count_in = 0
    count_out = 0
    
    if not json.os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

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
                if key in seen_keys: continue
                seen_keys.add(key)
                f_out.write(json.dumps(item, ensure_ascii=False) + '\n')
                count_out += 1
            except: continue
            
    print(f"DONE Step 4. Input: {count_in} | Output: {count_out}")

if __name__ == "__main__":
    import os
    json.os = os # Patch for script
    run()
