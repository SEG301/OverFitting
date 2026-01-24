import json
from pathlib import Path

# Input từ bước 2 (đã clean)
DATA_FILE = Path("data/02_cleaned.jsonl")
REVIEW_FILE = Path("data/reviews_itviec.jsonl")
OUTPUT_FILE = Path("data/03_with_itviec.jsonl")

def normalize_text(text):
    if not text: return ""
    return text.lower().strip()

def run():
    print("Step 3: Mapping ITviec Reviews...")
    
    # Load Reviews
    reviews_map = {}
    print("Loading ITviec reviews...")
    with open(REVIEW_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                rev = json.loads(line)
                name = normalize_text(rev.get('company_name'))
                if name:
                    if name not in reviews_map: reviews_map[name] = []
                    reviews_map[name].append(rev)
            except: continue
    print(f"Loaded {len(reviews_map)} companies with reviews.")
            
    # Map to Master
    matched = 0
    count = 0
    with open(DATA_FILE, 'r', encoding='utf-8') as f_in, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            try:
                item = json.loads(line)
                name = normalize_text(item.get('company_name'))
                
                if name in reviews_map:
                    item['reviews'] = reviews_map[name]
                    matched += 1
                
                f_out.write(json.dumps(item, ensure_ascii=False) + '\n')
                count += 1
                
                if count % 100000 == 0:
                    print(f"Processed {count}, matched {matched}...", end='\r')
            except: continue
            
    print(f"\nDONE Step 3. Matched {matched} companies.")
    print(f"Output: {OUTPUT_FILE}")

if __name__ == "__main__":
    run()
