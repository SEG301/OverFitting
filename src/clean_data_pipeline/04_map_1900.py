import json
from pathlib import Path
import re
import unicodedata

# Input từ bước 3
DATA_FILE = Path("data/03_with_itviec.jsonl")
REVIEW_FILE = Path("data/reviews_1900_detailed.jsonl")
OUTPUT_FILE = Path("data/04_with_all_reviews.jsonl")

def normalize_text(text):
    if not text: return ""
    text = text.lower()
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return " ".join(text.split())

def run():
    print("Step 4: Mapping 1900 Reviews...")
    
    reviews_1900 = {}
    print("Loading 1900 reviews...")
    with open(REVIEW_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                name = normalize_text(data.get('company_name_origin', ''))
                if not name: continue
                
                if name not in reviews_1900: reviews_1900[name] = []
                revs = data.get('reviews', [])
                if isinstance(revs, list):
                    reviews_1900[name].extend(revs)
            except: continue
    print(f"Loaded {len(reviews_1900)} companies with 1900 reviews.")

    matched = 0
    count = 0
    with open(DATA_FILE, 'r', encoding='utf-8') as f_in, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            try:
                item = json.loads(line)
                name_norm = normalize_text(item.get('company_name'))
                
                if name_norm in reviews_1900:
                    current = item.get('reviews', [])
                    current.extend(reviews_1900[name_norm])
                    item['reviews'] = current
                    matched += 1
                
                f_out.write(json.dumps(item, ensure_ascii=False) + '\n')
                count += 1
                
                if count % 100000 == 0:
                    print(f"Processed {count}, matched {matched}...", end='\r')
            except: continue

    print(f"\nDONE Step 4. Matched {matched} companies.")
    print(f"Output: {OUTPUT_FILE}")

if __name__ == "__main__":
    run()
