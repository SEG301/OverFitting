import json
from pathlib import Path

# Cấu hình đường dẫn file
INPUT_FILES = [
    Path("data/milestone1_final_deep_1m.jsonl"),
    Path("data/3cities_data.jsonl")
]
OUTPUT_FILE = Path("data/merged_data_cleaned.jsonl")

def normalize_text(text):
    """Chuẩn hóa text đơn giản để so sánh chính xác hơn"""
    if not text:
        return ""
    return text.strip().lower()

def merge_and_deduplicate():
    print(f"Bắt đầu gộp và lọc trùng từ {len(INPUT_FILES)} file...")
    
    seen_keys = set()
    total_records = 0
    unique_records = 0
    duplicates = 0
    
    # Tạo thư mục output nếu chưa có
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        for input_path in INPUT_FILES:
            if not input_path.exists():
                print(f"⚠️ Cảnh báo: Không tìm thấy file {input_path}, bỏ qua.")
                continue
                
            print(f"-> Đang xử lý file: {input_path.name}...")
            
            try:
                with open(input_path, 'r', encoding='utf-8') as f_in:
                    for line in f_in:
                        line = line.strip()
                        if not line: continue
                        
                        try:
                            # Parse JSON
                            item = json.loads(line)
                            total_records += 1
                            
                            # Tạo khóa định danh duy nhất (Tax + Name + Address)
                            # Dùng tuple để hash được và lưu vào set
                            tax = normalize_text(item.get('tax_code', ''))
                            name = normalize_text(item.get('company_name', ''))
                            addr = normalize_text(item.get('address', ''))
                            
                            # Khóa nhận diện trùng lặp
                            unique_key = (tax, name, addr)
                            
                            # Kiểm tra trùng
                            if unique_key in seen_keys:
                                duplicates += 1
                                continue
                            
                            # Nếu chưa trùng thì thêm vào set và ghi file
                            seen_keys.add(unique_key)
                            f_out.write(json.dumps(item, ensure_ascii=False) + '\n')
                            unique_records += 1
                            
                            # Log tiến độ mỗi 50k dòng
                            if total_records % 50000 == 0:
                                print(f"   Đã quét {total_records:,} dòng... (Unique: {unique_records:,})")
                                
                        except json.JSONDecodeError:
                            continue
                            
            except Exception as e:
                print(f"❌ Lỗi khi đọc file {input_path}: {e}")

    print("\n" + "="*40)
    print("KẾT QUẢ GỘP DỮ LIỆU")
    print("="*40)
    print(f"Tổng số dòng đã đọc  : {total_records:,}")
    print(f"Số dòng bị trùng lặp : {duplicates:,}")
    print(f"Số dòng duy nhất giữ lại: {unique_records:,}")
    print(f"File kết quả: {OUTPUT_FILE}")
    print("="*40)

if __name__ == "__main__":
    merge_and_deduplicate()
