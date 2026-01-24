import json
import re
import sys
from pyvi import ViTokenizer

# Input từ bước 4
INPUT_FILE = "data/04_with_all_reviews.jsonl"
OUTPUT_FILE = "data/05_final_segmented.jsonl"

# Check tiếng Việt
VIETNAMESE_CHARS = re.compile(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', re.IGNORECASE)

def is_vietnamese(text):
    if not text: return False
    return bool(VIETNAMESE_CHARS.search(text))

def safe_segment(text, check_lang=False):
    if not text or not isinstance(text, str): return ""
    if check_lang and not is_vietnamese(text):
        return text  # Giữ nguyên nếu không phải tiếng Việt
    try:
        return ViTokenizer.tokenize(text)
    except:
        return text

def run():
    print("Step 5: Segmenting Data (Vietnamese only for reviews)...")
    count = 0
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f_in, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        
        for line in f_in:
            if not line.strip(): continue
            try:
                item = json.loads(line)
                
                # Segment các field chính
                if 'company_name' in item:
                    item['company_name_seg'] = safe_segment(item['company_name'])
                if 'representative' in item:
                    item['representative_seg'] = safe_segment(item['representative'])
                if 'status' in item:
                    item['status_seg'] = safe_segment(item['status'])
                    
                # Industries
                inds = item.get('industries_detail', [])
                if inds:
                    ind_names = [ind.get('name', '') for ind in inds]
                    item['industries_arr_seg'] = [safe_segment(n) for n in ind_names]
                    item['industries_str_seg'] = " ".join(item['industries_arr_seg'])
                
                # Reviews - CHỈ segment tiếng Việt
                revs = item.get('reviews', [])
                if revs:
                    for r in revs:
                        r['content_seg'] = safe_segment(r.get('content', ''), check_lang=True)
                        r['title_seg'] = safe_segment(r.get('title', ''), check_lang=True)
                    item['reviews'] = revs
                
                f_out.write(json.dumps(item, ensure_ascii=False) + '\n')
                count += 1
                
                if count % 50000 == 0:
                    print(f"Segmented {count}...", end='\r')
                    
            except: continue

    print(f"\nDONE Step 5. Segmented {count} records.")
    print(f"Output: {OUTPUT_FILE}")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    run()
