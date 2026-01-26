import json
import re
import sys
from pyvi import ViTokenizer

# Input từ bước 1 (đã dedup)
INPUT_FILE = "data/01_deduplicated.jsonl"
OUTPUT_FILE = "data/02_cleaned.jsonl"

# ============ UTILITY ============

def strip_html(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&nbsp;', ' ', text)
    text = re.sub(r'&amp;', '&', text)
    text = re.sub(r'&#\d+;', '', text)
    return text

def is_mostly_uppercase(text):
    if not text: return False
    letters = [c for c in text if c.isalpha()]
    if not letters: return False
    return (sum(1 for c in letters if c.isupper()) / len(letters)) > 0.5

# ============ FIX FUNCTIONS ============

def fix_company_name(name):
    if not name or not isinstance(name, str): return ""
    
    # STRICT CHECK: Nếu có ký tự  (U+FFFD) -> XÓA LUÔN DÒNG
    if '\uFFFD' in name or '' in name:
        return None
    
    name = strip_html(name)
    name = name.replace("^", " ") # Fix lỗi Caret
    # name = name.replace('\uFFFD', '') # Không cần nữa vì đã xóa dòng ở trên
    name = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', name)
    name = " ".join(name.split())
    
    if is_mostly_uppercase(name):
        name = name.title()
        for wrong, right in {'Tnhh': 'TNHH', 'Cp': 'CP', 'Xnk': 'XNK', 'Tm': 'TM', 'Dv': 'DV', 'Sx': 'SX'}.items():
            name = name.replace(wrong, right)
    
    return name.strip()

def fix_representative(rep):
    if not rep or not isinstance(rep, str): return ""
    
    rep = strip_html(rep)
    rep = re.sub(r'\d+', '', rep)
    rep = re.sub(r'[^\w\s.\-]', '', rep, flags=re.UNICODE)
    rep = " ".join(rep.split())
    
    if is_mostly_uppercase(rep):
        rep = rep.title()
    
    return rep.strip()

def fix_address_text(addr):
    if not addr or not isinstance(addr, str): return ""
    
    # STRICT CHECK: Nếu có ký tự  (U+FFFD) -> XÓA LUÔN DÒNG
    if '\uFFFD' in addr:
        return None
    
    # 2. Xóa HTML & Caret (^)
    addr = strip_html(addr)
    addr = addr.replace("^", " ") # Fix lỗi Caret
    addr = addr.strip()
    
    # 3. Tách từ dính (Bổ sung: Sô, Ô, Lầu...)
    # Keywords gốc: Số|Tầng|Lô|Nhà|Phòng|Khu|Ngõ|Ngách|Hẻm|Đường|Phố|Quận|Huyện|Xã|Phường|Thị Trấn|SO
    # Mới thêm: Sô|Ô|Lầu
    keywords = r'Số|Sô|Tầng|Lầu|Lô|Nhà|Ô|Phòng|Khu|Ngõ|Ngách|Hẻm|Đường|Phố|Quận|Huyện|Xã|Phường|Thị Trấn|SO'
    
    addr = re.sub(r'(' + keywords + r')([0-9]+)', r'\1 \2', addr, flags=re.IGNORECASE)
    addr = re.sub(r'([0-9])(' + keywords + r')', r'\1 \2', addr, flags=re.IGNORECASE)
    
    def normalize_kw(m):
        kw, rest = m.group(1), m.group(2)
        if kw.upper() == 'SO': return 'SO' + rest
        kw_title = kw.title()
        # Chuẩn hóa keyword viết sai chính tả
        if kw_title == 'Sô': return 'Số' + rest
        return kw_title + rest
    
    addr = re.sub(r'\b(' + keywords + r')(\s+)', normalize_kw, addr, flags=re.IGNORECASE)
    addr = re.sub(r',([^\s])', r', \1', addr)
    addr = " ".join(addr.split())
    
    if is_mostly_uppercase(addr):
        addr = addr.title()
        addr = addr.replace("Tp.", "TP.").replace("Tphcm", "TP.HCM")

    return addr

# ============ MAIN ============

def run():
    print("Step 2: Fixing Data Errors (Name + Rep + Address)...")
    count = 0
    skipped_bad_char = 0
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f_in, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            if not line.strip(): continue
            try:
                item = json.loads(line)
                
                # Fix Company Name
                fixed_name = fix_company_name(item.get('company_name', ''))
                # Nếu fix_company_name trả về None -> SKIP
                if fixed_name is None:
                    skipped_bad_char += 1
                    continue
                
                # Fix Address
                fixed_addr = fix_address_text(item.get('address', ''))
                # Nếu fix_address_text trả về None (có lỗi ) -> SKIP
                if fixed_addr is None:
                    skipped_bad_char += 1
                    continue
                
                item['company_name'] = fixed_name
                item['representative'] = fix_representative(item.get('representative', ''))
                item['address'] = fixed_addr
                item['address_seg'] = ViTokenizer.tokenize(item['address']) if item['address'] else ""
                
                f_out.write(json.dumps(item, ensure_ascii=False) + '\n')
                count += 1
                
                if count % 100000 == 0:
                    print(f"Fixed {count} (Skipped {skipped_bad_char} bad records)...", end='\r')
            except: continue
            
    print(f"\nDONE Step 2. Fixed {count} records.")
    print(f"Skipped {skipped_bad_char} records containing bad characters ().")
    print(f"Output: {OUTPUT_FILE}")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    run()

