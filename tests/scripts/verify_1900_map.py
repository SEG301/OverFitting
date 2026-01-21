import json
import sys

# Đảm bảo in ra tiếng Việt không bị lỗi trên Windows Console
sys.stdout.reconfigure(encoding='utf-8')

INPUT_FILE = "data/final_data_full_reviews.jsonl"

def check_mapping_quality():
    print(f"--- KIỂM TRA MẪU KHỚP NỐI (DATA GỐC <--> 1900 REVIEW) ---")
    
    count = 0
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                reviews = data.get('reviews', [])
                
                # Tìm review có nguồn là '1900'
                r_1900 = [r for r in reviews if r.get('source') == '1900']
                
                if r_1900:
                    master_name = data.get('company_name', 'No Name')
                    source_name = r_1900[0].get('company_name_on_source', 'No Source Name')
                    address = data.get('address', 'No Address')
                    
                    print(f"[{count+1}]")
                    print(f"   Master Data: {master_name}")
                    print(f"   1900 Source: {source_name}")
                    print(f"   Address:     {address}")
                    print("   ------------------------------------------------")
                    
                    count += 1
                    if count >= 10: break # Kiểm tra 10 mẫu đầu tiên
            except Exception as e:
                continue

    if count == 0:
        print("Không tìm thấy công ty nào được map với nguồn '1900'.")

if __name__ == "__main__":
    check_mapping_quality()
