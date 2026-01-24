import json
from pathlib import Path
import re
import unicodedata

# PATHS
DATA_FILE = Path("data/enterprise_data.jsonl")      # Data from Stage 1
ITVIEC_FILE = Path("data/reviews_itviec.jsonl")
R1900_FILE = Path("data/reviews_1900.jsonl")
OUTPUT_FILE = Path("data/00_mapped_data.jsonl")

def normalize_text(text):
    if not text: return ""
    text = text.lower()
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return " ".join(text.split())

def remove_legal_terms(text):
    text = normalize_text(text)
    for pat in [r'\bcong ty\b', r'\btnhh\b', r'\bcp\b', r'\bjsc\b', r'\bltd\b']:
        text = re.sub(pat, '', text)
    return text.strip()

def load_reviews(file_path, is_itviec=True):
    print(f"Loading reviews from {file_path}...")
    rev_map = {}
    if not file_path.exists(): return rev_map
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                item = json.loads(line)
                # Logic to map by name...
                name = remove_legal_terms(item.get('company_name', ''))
                if not name and is_itviec:
                    # Extract from URL for ITviec
                    match = re.search(r'/companies/([\w-]+)', item.get('url', ''))
                    if match: name = normalize_text(match.group(1).replace('-', ' '))
                
                if name not in rev_map: rev_map[name] = []
                rev_map[name].append(item)
            except: pass
    return rev_map

def run():
    print("Step 3: Mapping Reviews to Enterprise Data...")
    it_revs = load_reviews(ITVIEC_FILE, True)
    r1900_revs = load_reviews(R1900_FILE, False)
    
    if not DATA_FILE.exists():
        print(f"Error: {DATA_FILE} not found. Run InfoDoanhNghiep crawler first.")
        return

    count = 0
    with open(DATA_FILE, 'r', encoding='utf-8') as f_in, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            try:
                item = json.loads(line)
                m_name = remove_legal_terms(item.get('company_name', ''))
                
                # Simple Merge
                merged_revs = it_revs.get(m_name, []) + r1900_revs.get(m_name, [])
                if merged_revs:
                    item['reviews'] = merged_revs
                    item['has_review'] = True
                    count += 1
                
                f_out.write(json.dumps(item, ensure_ascii=False) + '\n')
            except: pass
            
    print(f"DONE Step 3. Matched {count} companies.")

if __name__ == "__main__":
    run()
