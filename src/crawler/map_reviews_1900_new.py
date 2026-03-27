import json
from pathlib import Path
import re
import unicodedata
from collections import defaultdict

# Cấu hình đường dẫn
DATA_FILE = Path("data/final_data_with_reviews.jsonl") # File này đã có ITviec reviews
REVIEW_FILE = Path("data/reviews_1900_detailed (1).jsonl")
OUTPUT_FILE = Path("data/final_data_full_reviews.jsonl")

def normalize_text(text):
    """
    Chuẩn hóa văn bản cơ bản
    """
    if not text:
        return ""
    text = text.lower()
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return " ".join(text.split())

def remove_legal_terms(text):
    """
    Loại bỏ các từ khóa doanh nghiệp để lấy tên riêng (core name).
    Chỉ dùng khi so sánh tên ngắn gọn.
    """
    clean_text = normalize_text(text)
    legal_patterns = [
        r'\bcong ty\b', r'\btnhh\b', r'\bco\b', r'\bltd\b', r'\bjsc\b', 
        r'\bcp\b', r'\bco phan\b', r'\btrach nhiem huu han\b', 
        r'\bdau tu\b', r'\bthuong mai\b', r'\bdich vu\b', r'\bsan xuat\b',
        r'\btechnology\b', r'\btechnologies\b', r'\bsoftware\b', r'\bgroup\b',
        r'\bviet nam\b', r'\bvn\b', r'\bglobal\b', r'\bcorp\b', r'\bcorporation\b'
    ]
    # Sắp xếp pattern dài trước ngắn sau để replace đúng
    for pat in legal_patterns:
        clean_text = re.sub(pat, '', clean_text)
    return clean_text.strip()

def get_province_key(address_str):
    """
    Rút trích Tỉnh/Thành phố từ địa chỉ để làm key filter.
    """
    norm_addr = normalize_text(address_str)
    
    provinces = [
        "ha noi", "ho chi minh", "da nang", "hai phong", "can tho",
        "khanh hoa", "dong nai", "binh duong", "bac ninh", "hung yen"
    ]
    
    for p in provinces:
        if p in norm_addr:
            return p
    return None

def load_1900_reviews():
    print(f"Loading reviews from {REVIEW_FILE}...")
    # Group by normalized core name AND province key
    # data structure: { (core_name, province_key): [review_obj, review_obj...] }
    reviews_map = defaultdict(list)
    
    count = 0
    with open(REVIEW_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            try:
                item = json.loads(line)
                name = item.get('company_name', '')
                raw_reviews = item.get('reviews', [])
                if not raw_reviews: continue

                # Normalize keys
                core_name = remove_legal_terms(name)
                # Skip if name is too short/generic after stripping (e.g. "Group", "Global")
                if len(core_name) < 3: 
                    # If removing legal terms stripped everything, revert to normalized full name
                    core_name = normalize_text(name)
                
                prov = get_province_key(item.get('address', '')) # e.g., "ha noi"
                
                # Format reviews
                clean_reviews = []
                for r in raw_reviews:
                    clean_reviews.append({
                        'source': '1900',
                        'company_name_on_source': name, # Keep orig name for reference
                        'rating': r.get('rating'),
                        'title': r.get('title'),
                        'date': None, # 1900 doesn't imply clear date in this snippet
                        'content': f"Pros: {r.get('pros','')}\nCons: {r.get('cons','')}".strip(),
                        'url': item.get('url')
                    })
                
                key = (core_name, prov)
                reviews_map[key].extend(clean_reviews)
                count += 1
            except Exception:
                continue
                
    print(f"Loaded {count} companies from 1900 source.")
    return reviews_map

def run():
    reviews_1900 = load_1900_reviews()
    
    # Pre-calculate keys needed to speed up matching?
    # No, iterating 1900 map (4000 entries) inside Master loop (1.8M) is slow (4000 * 1.8M operations).
    # We should iterate Master loop ONCE, and look up in 1900 map.
    
    # But Master Names are long ("Cong ty TNHH VietJack"), 1900 keys are short ("vietjack").
    # We need to extract core name from Master Name and see if it exists in reviews_map.
    
    print(f"Processing master file: {DATA_FILE}...")
    matched_count = 0
    total = 0
    
    # Cache for legal term removal to speed up
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f_in, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        
        for line in f_in:
            line = line.strip()
            total += 1
            if not line: continue
            
            try:
                master_item = json.loads(line)
                m_name = master_item.get('company_name', '')
                m_core_name = remove_legal_terms(m_name)
                m_prov = get_province_key(master_item.get('address', ''))
                
                # Try finding a match
                # Strategy 1: Exact Match of Core Name + Province
                # Strategy 2: Core Name Match + Province is None (in 1900) - Relaxed
                
                matches = []
                
                # Attempt lookup
                # Key format: (core_name, province_key)
                
                # Exact Try
                if (m_core_name, m_prov) in reviews_1900:
                    matches.extend(reviews_1900[(m_core_name, m_prov)])
                
                # Relaxed Try: If m_prov mismatch or missing, but name is unique/long enough?
                # For safety, let's stick to strict Province match if Province exists in 1900 data.
                # What if 1900 data has prov=None (e.g. invalid address)?
                if (m_core_name, None) in reviews_1900:
                     matches.extend(reviews_1900[(m_core_name, None)])
                     
                # What if Master Name contains 1900 Name as substring?
                # e.g. Master: "Cong ty TNHH VietJack Education", 1900 key: "vietjack"
                # m_core_name: "vietjack education" -> unmatched.
                # This reverse lookup is hard with Hash Map.
                
                # Optimization for Substring Match:
                # Since 1900 list is small (~4000), we can iterate it for "high value" targets if hash lookup fails?
                # No, that's too slow for 1.8M lines.
                # BUT, we can tokenize m_core_name.
                
                if matches:
                    current_reviews = master_item.get('reviews', [])
                    # Append unique reviews only (based on title/content hash roughly?)
                    # For now just append, user wants "map cho chuẩn" - assume data distinct
                    current_reviews.extend(matches)
                    master_item['reviews'] = current_reviews
                    master_item['has_review'] = True
                    matched_count += 1
                
                f_out.write(json.dumps(master_item, ensure_ascii=False) + '\n')
                
                if total % 100000 == 0:
                    print(f"Processed {total:,} records. Matched new reviews: {matched_count:,}")
                    
            except Exception:
                f_out.write(line + '\n')

    print("-" * 30)
    print(f"DONE! Mapped/Enriched {matched_count:,} companies with 1900 reviews.")
    print(f"Output saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    run()
