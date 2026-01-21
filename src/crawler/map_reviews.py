import json
from pathlib import Path
import re
from unicodedata import normalize as unicode_normalize

# Cấu hình đường dẫn
DATA_FILE = Path("data/merged_data_cleaned.jsonl")
REVIEW_FILE = Path("data/reviews_1900_detailed.jsonl")
OUTPUT_FILE = Path("data/final_data_with_reviews.jsonl")

def normalize_name(text):
    """
    Chuẩn hóa tên công ty để tăng khả năng map chính xác.
    - Chuyển về chữ thường
    - Loại bỏ dấu tiếng Việt (nếu cần thiết, nhưng nên giữ để chính xác hơn)
    - Loại bỏ các từ khóa pháp lý thông dụng (Công ty, TNHH, CP...)
    """
    if not text:
        return ""
    
    # 1. Chuyển chữ thường
    text = text.lower().strip()
    
    # 2. Loại bỏ các tiền tố/hậu tố pháp lý phổ biến
    remove_patterns = [
        r'công ty\s+tnhh\s+mtv', r'công ty\s+tnhh', r'công ty\s+cp', 
        r'công ty\s+cổ\s+phần', r'doanh\s+nghiệp\s+tn', r'dntn', 
        r'tnhh', r'jsc', r'co\.,ltd', r'corp'
    ]
    
    for pat in remove_patterns:
        text = re.sub(pat, '', text)
        
    # 3. Xử lý khoảng trắng thừa và ký tự đặc biệt
    text = re.sub(r'[^\w\s]', ' ', text) # Bỏ dấu chấm phẩy
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def load_reviews():
    print(f"Loading reviews from {REVIEW_FILE}...")
    review_map = {}
    count = 0
    
    if not REVIEW_FILE.exists():
        print("Review file not found!")
        return {}

    with open(REVIEW_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                item = json.loads(line)
                raw_name = item.get('name', '')
                
                # Chuẩn hóa tên làm key
                norm_name = normalize_name(raw_name)
                
                if norm_name:
                    # Lưu lại toàn bộ object review hoặc chỉ list reviews
                    # Ở đây ta lưu list reviews để gộp vào data chính
                    if norm_name not in review_map:
                        review_map[norm_name] = []
                    
                    # File review structure: {"name": "...", "reviews": [...]}
                    reviews = item.get('reviews', [])
                    review_map[norm_name].extend(reviews)
                    count += 1
            except json.JSONDecodeError:
                continue
                
    print(f"Loaded {count} review entries. Unique normalized names: {len(review_map)}")
    return review_map

def map_and_merge():
    review_map = load_reviews()
    if not review_map:
        print("No reviews to map. Exiting.")
        return

    print(f"Processing master data from {DATA_FILE}...")
    
    matched_count = 0
    total_count = 0
    
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f_in, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        
        for line in f_in:
            line = line.strip()
            total_count += 1
            if not line: continue
            
            try:
                company = json.loads(line)
                raw_name = company.get('company_name', '')
                
                # Chuẩn hóa tên từ data gốc
                norm_name = normalize_name(raw_name)
                
                # Tra cứu trong map review
                if norm_name in review_map:
                    # TÌM THẤY! -> Merge reviews vào
                    company['reviews'] = review_map[norm_name]
                    # Đánh dấu là có review để dễ lọc sau này
                    company['has_review'] = True 
                    matched_count += 1
                else:
                    company['has_review'] = False
                
                # Ghi ra file mới
                f_out.write(json.dumps(company, ensure_ascii=False) + '\n')
                
                if total_count % 100000 == 0:
                    print(f"Processed {total_count:,} records... (Matched: {matched_count:,})")
                    
            except json.JSONDecodeError:
                continue

    print("\n" + "="*40)
    print("MAPPING COMPLETE")
    print("="*40)
    print(f"Total Companies Processed: {total_count:,}")
    print(f"Companies with Reviews Found: {matched_count:,}")
    print(f"Output File: {OUTPUT_FILE}")
    print("="*40)

if __name__ == "__main__":
    map_and_merge()
