import json
from pathlib import Path
import re
import unicodedata

# Cấu hình đường dẫn
DATA_FILE = Path("data/merged_data_cleaned.jsonl")
REVIEW_FILE = Path("data/reviews_itviec.jsonl")
OUTPUT_FILE = Path("data/final_data_with_reviews.jsonl")

def normalize_text(text):
    """
    Chuẩn hóa văn bản:
    - Chuyển thành chữ thường
    - Bỏ dấu tiếng Việt (Hà Nội -> ha noi)
    - Bỏ ký tự đặc biệt
    """
    if not text:
        return ""
    
    # 1. Chuyển chữ thường
    text = text.lower()
    
    # 2. Bỏ dấu tiếng Việt (Normal Form D)
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    
    # 3. Loại bỏ từ khóa pháp lý (công ty, tnhh...) để so sánh tên
    remove_patterns = [
        r'\bcong ty\b', r'\btnhh\b', r'\bcp\b', r'\bco\.,\s*ltd\b', 
        r'\bviet nam\b', r'\bjsc\b', r'\bcorp\b', r'\binc\b',
        r'\bgroup\b', r'\bholdings\b', r'\bbranch\b'
    ]
    for pat in remove_patterns:
        text = re.sub(pat, '', text)

    # 4. Giữ lại chữ cái và số, bỏ ký tự đặc biệt
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    
    return " ".join(text.split())

def parse_itviec_address(addr_str):
    """
    Tách địa chỉ ITviec (thường có nhiều chi nhánh ngăn cách bởi |)
    Trả về list các địa chỉ đã chuẩn hóa
    """
    if not addr_str:
        return []
    parts = addr_str.split('|')
    return [normalize_text(p) for p in parts]

def load_itviec_reviews():
    print(f"Loading reviews from {REVIEW_FILE}...")
    companies = {} # Key: normalized_name, Value: {reviews: [], addresses: []}
    
    count = 0
    with open(REVIEW_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            try:
                # ITviec review format is flat, each line is a review
                # We need to extract company info from URL or we rely on 'company_address' 
                # Wait, ITviec file doesn't have 'company_name' explicit field in the sample?
                # Looking at sample: "url": "https://itviec.com/companies/mb-bank/review"
                # We can extract name from URL slug: "mb-bank"
                
                rev = json.loads(line)
                url = rev.get('url', '')
                
                # Extract simplified company identifier from URL
                # e.g. .../companies/mb-bank/review -> mb bank
                match = re.search(r'/companies/([\w-]+)', url)
                if not match: 
                    continue
                
                slug_name = match.group(1).replace('-', ' ')
                norm_name = normalize_text(slug_name)
                
                if norm_name not in companies:
                    companies[norm_name] = {
                        'reviews': [],
                        'addresses': parse_itviec_address(rev.get('company_address', ''))
                    }
                
                # Simplify review object to save space
                clean_review = {
                    'source': 'Itviec',
                    'rating': rev.get('rating'),
                    'title': rev.get('title'),
                    'date': rev.get('date'),
                    'content': f"Liked: {rev.get('liked', '')}\nImprovements: {rev.get('improvements', '')}".strip()
                }
                companies[norm_name]['reviews'].append(clean_review)
                count += 1
            except Exception as e:
                continue
                
    print(f"Loaded {count} reviews for {len(companies)} unique companies.")
    return companies

def check_address_match(master_addr_norm, itviec_addrs):
    """
    Kiểm tra xem địa chỉ master có khớp với bất kỳ địa chỉ nào của ITviec không.
    Logic: Kiểm tra xem Tỉnh/Thành phố hoặc Quận/Huyện có trùng nhau không.
    """
    if not master_addr_norm or not itviec_addrs:
        # Nếu không có địa chỉ để so sánh, chấp nhận rủi ro match bằng tên (hoặc trả về False nếu muốn chặt chẽ)
        # Ở đây ta trả về True nhưng log warning ngầm (chấp nhận match tên nếu tên quá giống)
        return True 
        
    for it_addr in itviec_addrs:
        # Check if CITY matches (ha noi, ho chi minh, da nang...)
        # Simple substring check suffices for now
        if "ha noi" in master_addr_norm and "ha noi" in it_addr: return True
        if "ho chi minh" in master_addr_norm and "ho chi minh" in it_addr: return True
        if "da nang" in master_addr_norm and "da nang" in it_addr: return True
        
        # Check token overlap ratio for more robustness
        master_tokens = set(master_addr_norm.split())
        it_tokens = set(it_addr.split())
        common = master_tokens.intersection(it_tokens)
        if len(common) >= 3: # Ít nhất 3 từ giống nhau (vd: quan, dong, da)
            return True
            
    return False

def run():
    itviec_data = load_itviec_reviews()
    
    print(f"Processing master file: {DATA_FILE}...")
    matched = 0
    total = 0
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f_in, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        
        for line in f_in:
            line = line.strip()
            total += 1
            if not line: continue
            
            try:
                master_item = json.loads(line)
                m_name = normalize_text(master_item.get('company_name', ''))
                m_addr = normalize_text(master_item.get('address', ''))
                
                reviews_to_add = []
                
                # Check match with ITviec
                # 1. Exact Name substring match (e.g. 'kms technology' in 'cong ty tnhh kms technology viet nam')
                # Iterate all itviec companies (This is slow O(N*M), but M is small ~300 companies)
                # Optimization: Direct lookup if keys match exactly, else fuzzy.
                
                for it_name, it_data in itviec_data.items():
                    # Simple fuzzy check: is the short ITviec name inside the long Master name?
                    if it_name in m_name:
                        # 2. Address Validation
                        if check_address_match(m_addr, it_data['addresses']):
                            reviews_to_add.extend(it_data['reviews'])
                            # Don't break, maybe match multiple? No, usually one is enough.
                            break 
                            
                if reviews_to_add:
                    # Append strictly to 'reviews' list
                    current_reviews = master_item.get('reviews', [])
                    current_reviews.extend(reviews_to_add)
                    master_item['reviews'] = current_reviews
                    master_item['has_review'] = True
                    matched += 1
                
                f_out.write(json.dumps(master_item, ensure_ascii=False) + '\n')
                
                if total % 100000 == 0:
                    print(f"Processed {total:,} records. Matched: {matched:,}")
                    
            except Exception:
                continue

    print("-" * 30)
    print(f"DONE! Mapped {matched:,} companies with ITviec reviews.")
    print(f"Output saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    run()
