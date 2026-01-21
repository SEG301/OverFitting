import json
from pyvi import ViTokenizer
import sys

# Cấu hình
INPUT_FILE = "data/final_data_full_reviews.jsonl"
OUTPUT_FILE = "data/final_data_segmented.jsonl"

def safe_segment(text):
    if not text or not isinstance(text, str):
        return ""
    try:
        # PyVi tách từ: "Hà Nội" -> "Hà_Nội"
        return ViTokenizer.tokenize(text)
    except:
        return text

def run_segmentation():
    print("Start segmenting extra fields...")
    count = 0
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f_in, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        
        for line in f_in:
            line = line.strip()
            if not line: continue
            
            try:
                item = json.loads(line)
                
                # 1. Representative
                if 'representative' in item:
                    item['representative_seg'] = safe_segment(item['representative'])
                
                # 2. Status
                if 'status' in item:
                    item['status_seg'] = safe_segment(item['status'])
                    
                # 3. Industries (Lấy danh sách tên ngành, nối lại rồi tách)
                inds = item.get('industries_detail', [])
                if inds:
                    # Tạo list tên ngành đã segment để search
                    ind_names = [ind.get('name', '') for ind in inds]
                    # Nối lại thành 1 chuỗi dài để segment 1 lần cho nhanh, hoặc segment từng cái
                    # Segment từng cái để giữ cấu trúc mảng sẽ linh hoạt hơn
                    item['industries_arr_seg'] = [safe_segment(name) for name in ind_names]
                    # Hoặc tạo 1 field text full để search fulltext
                    item['industries_str_seg'] = " ".join(item['industries_arr_seg'])
                
                # 4. Reviews
                revs = item.get('reviews', [])
                if revs:
                    # Segment nội dung từng review
                    for r in revs:
                        r['content_seg'] = safe_segment(r.get('content', ''))
                        r['title_seg'] = safe_segment(r.get('title', ''))
                    # Cập nhật lại list reviews (đã có field _seg bên trong từng object con)
                    item['reviews'] = revs
                
                f_out.write(json.dumps(item, ensure_ascii=False) + '\n')
                
                count += 1
                if count % 10000 == 0:
                    print(f"Segmented {count} records...", end='\r')
                    
            except Exception as e:
                print(f"Error parse line: {e}")
                continue

    print(f"\nDONE! Segmented {count} records.")
    print(f"Output: {OUTPUT_FILE}")

if __name__ == "__main__":
    run_segmentation()
