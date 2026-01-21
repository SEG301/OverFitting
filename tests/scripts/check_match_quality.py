import json
import sys

# Set output to utf-8
sys.stdout.reconfigure(encoding='utf-8')

def check():
    print("--- KIỂM TRA KHỚP DỮ LIỆU ---")
    with open('data/final_data_with_reviews.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if '"has_review": true' in line:
                data = json.loads(line)
                print(f"1. DATA GỐC (Master File):")
                print(f"   - Tên:    {data.get('company_name')}")
                print(f"   - Địa chỉ: {data.get('address')}")
                print(f"   - MST:    {data.get('tax_code')}")
                
                print(f"\n2. REVIEW ĐƯỢC MAP VÀO:")
                reviews = data.get('reviews', [])
                if reviews:
                    r = reviews[0]
                    print(f"   - Nguồn:  {r.get('source')}")
                    print(f"   - Title:  {r.get('title')}")
                    print(f"   - Date:   {r.get('date')}")
                    # ITviec reviews không lưu lại tên công ty gốc trong object review con,
                    # nhưng ta có thể đoán qua nội dung hoặc check lại logic map.
                
                print("\n-> ĐÁNH GIÁ: Bạn hãy nhìn Tên và Địa chỉ bên trên để xem có hợp lý không.")
                break

if __name__ == "__main__":
    check()
