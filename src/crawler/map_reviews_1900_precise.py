import json
from pathlib import Path
import re
import unicodedata
from collections import defaultdict

# Cấu hình file
DATA_FILE = Path("data/final_data_with_reviews.jsonl") # Input gốc (đã có ITviec)
REVIEW_FILE = Path("data/reviews_1900_detailed (1).jsonl")
OUTPUT_FILE = Path("data/final_data_full_reviews_precise.jsonl") # Output mới

def normalize_text(text):
    if not text: return ""
    text = text.lower()
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    return " ".join(text.split())

def get_core_tokens(text):
    """
    Tách từ khóa quan trọng, bỏ qua stop words doanh nghiệp.
    Trả về set các từ (tokens).
    """
    norm = normalize_text(text)
    tokens = norm.split()
    
    stop_words = {
        'cong', 'ty', 'tnhh', 'cp', 'co', 'ltd', 'jsc', 'thuong', 'mai', 'dich', 'vu', 
        'dau', 'tu', 'phat', 'trien', 'san', 'xuat', 'viet', 'nam', 'vn', 'toan', 'cau',
        'group', 'holdings', 'global', 'corp', 'corporation', 'chi', 'nhanh', 'joint', 'stock'
    }
    
    core_tokens = [t for t in tokens if t not in stop_words]
    
    # Nếu lọc hết stop words mà rỗng (VD: "Cong ty TNHH Thuong mai Dich vu"), 
    # thì giữ lại nguyên gốc để tránh lỗi, nhưng trường hợp này data rác.
    if not core_tokens:
        return set(tokens) # Fallback
        
    return set(core_tokens)

def is_safe_match(master_name, source_name, master_addr, source_addr_prov):
    """
    Kiểm tra độ an toàn khi map.
    1. Kiểm tra Tỉnh/Thành phố (BẮT BUỘC KHỚP nếu source có thông tin).
    2. Kiểm tra Tên:
       - Nếu Tên Source là tập con hoàn hảo của Tên Master (đã bỏ legal terms) -> OK.
       - Hoặc Jaccard Similarity (tỷ lệ từ trùng) > 0.7.
    """
    # 1. Check Address (Province level)
    # Rút trích tỉnh thành từ Master Address
    # List tỉnh thành simplified
    provinces = ["ha noi", "ho chi minh", "da nang", "hai phong", "can tho"]
    m_addr_norm = normalize_text(master_addr)
    
    matched_prov = False
    if not source_addr_prov:
        # Nếu source không có địa chỉ, risk cao -> yêu cầu tên phải cực giống
        pass 
    else:
        # Source addr thường là "Hà Nội" hoặc "Hồ Chí Minh"
        s_prov_norm = normalize_text(source_addr_prov)
        if s_prov_norm in m_addr_norm:
            matched_prov = True
        else:
            # Nếu Source có tỉnh mà Master không khớp tỉnh đó -> REJECT NGAY
            return False

    # 2. Check Name Similarity
    m_tokens = get_core_tokens(master_name)
    s_tokens = get_core_tokens(source_name)
    
    # Nếu tên quá ngắn (chỉ 1 từ) và từ đó phổ biến (Golden, Star, Sun...) -> REJECT nếu không khớp tỉnh
    if len(s_tokens) == 1 and not matched_prov:
        return False

    common = m_tokens.intersection(s_tokens)
    
    # RULE 1: Source tokens là tập con của Master tokens (VD: "Freetalk English" <= "Freetalk English Education")
    # Điều kiện: Phải khớp ít nhất 2 từ (để tránh khớp 1 từ "Solar") HOẶC khớp 1 từ nhưng từ đó rất dài/đặc biệt.
    is_subset = s_tokens.issubset(m_tokens)
    
    if is_subset:
        if len(s_tokens) >= 2: return True
        # Nếu chỉ 1 từ, từ đó phải dài > 4 ký tự (VD: "Viettel" ok, "T&P" risk)
        if len(s_tokens) == 1 and len(list(s_tokens)[0]) > 3: return True
        
    # RULE 2: Jaccard Similarity cho trường hợp viết tắt/đảo ngữ
    # VD: "Techcombank" vs "Ngan hang TMCP Ky Thuong" -> Cái này khó map bằng rule text, bỏ qua.
    # VD: "Samsung Electronics VN" vs "Samsung Vina"
    union = len(m_tokens.union(s_tokens))
    if union == 0: return False
    score = len(common) / union
    
    if score > 0.6: return True
    
    return False

def load_1900_reviews():
    print(f"Loading and indexing reviews from {REVIEW_FILE}...")
    reviews_list = []
    
    with open(REVIEW_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip(): continue
            try:
                item = json.loads(line)
                # Chỉ lấy item có review
                if not item.get('reviews'): continue
                
                # Pre-process for faster matching
                item['norm_name'] = normalize_text(item.get('company_name', ''))
                # Extract 'Hà Nội', 'HCM' from address field
                addr = item.get('address', '')
                item['prov_key'] = addr if addr in ['Hà Nội', 'Hồ Chí Minh', 'Đà Nẵng'] else "" # Simple filter
                
                reviews_list.append(item)
            except: continue
            
    print(f"Loaded {len(reviews_list)} review candidates.")
    return reviews_list

def run():
    candidates = load_1900_reviews()
    
    print(f"Processing matches with HIGH PRECISION logic...")
    matched_count = 0
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
                m_name = master_item.get('company_name', '')
                m_addr = master_item.get('address', '')
                
                reviews_to_add = []
                
                # Scan candidates (Slow O(N*M) but M is 4000, N is 1.8M -> 7.2B checks -> TOO SLOW!)
                # Cần tối ưu: Chỉ check những candidate có chung ít nhất 1 từ (First Token Indexing)
                
                # --- OPTIMIZATION: SKIP THIS CHECK FOR NORMAL USE ---
                # Vì Python loop chậm, ta không thể loop 4000 item cho mỗi 1.8M dòng.
                # Giải pháp:
                # 1. Build Index cho Candidates: Token -> List[CandidateIO]
                # 2. Với mỗi Master item, lấy tokens của nó -> look up Index -> lấy tập candidate tiềm năng -> check kỹ.
                pass 
            except: pass
    
    # REWRITE: Build Inverted Index First for Performance
    index = defaultdict(list)
    for idx, cand in enumerate(candidates):
        tokens = get_core_tokens(cand['norm_name'])
        for t in tokens:
            index[t].append(idx)
            
    print("Index built. Starting scan...")
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f_in, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
         
        for line in f_in:
            if not line.strip(): continue
            master_item = json.loads(line)
            
            m_name = master_item.get('company_name', '')
            m_addr = master_item.get('address', '')
            m_tokens = get_core_tokens(m_name)
            
            potential_indices = set()
            for t in m_tokens:
                if t in index:
                    potential_indices.update(index[t])
            
            matched_reviews = []
            
            for idx in potential_indices:
                cand = candidates[idx]
                if is_safe_match(m_name, cand['company_name'], m_addr, cand.get('address')):
                    # Format reviews
                    raw_reviews = cand.get('reviews', [])
                    clean = []
                    for r in raw_reviews:
                        clean.append({
                            'source': '1900',
                            'company_name_on_source': cand['company_name'],
                            'rating': r.get('rating'),
                            'title': r.get('title'),
                            'content': f"Pros: {r.get('pros','')}\nCons: {r.get('cons','')}".strip(),
                            'url': cand.get('url')
                        })
                    matched_reviews.extend(clean)
            
            if matched_reviews:
                curr = master_item.get('reviews', [])
                # Deduplicate? Assume distinct sources
                curr.extend(matched_reviews)
                master_item['reviews'] = curr
                master_item['has_review'] = True
                matched_count += 1
            
            f_out.write(json.dumps(master_item, ensure_ascii=False) + '\n')
            
            if total % 100000 == 0:
                 print(f"Processed {total} items... Matched: {matched_count}")
                 total += 1 # Just for loop counting sync
            else:
                total += 1

    print(f"DONE. Precise matches: {matched_count}")

if __name__ == "__main__":
    run()
