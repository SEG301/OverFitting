import os

LOG_FILE = "e:/Crwal/OverFitting/ai_log.md"

NEW_CONTENT = """

---

## Date: 2026-01-18 -> 2026-01-20
**Task:** Advanced Data Processing: Deduplication & Review Mapping.

**User:** Chúng ta đã có dữ liệu thô (1.8 triệu dòng) và các file review từ ITviec, 1900.com.vn. Hãy làm sạch và nối chúng lại với nhau.

**Phase 1: Deduplication (Lọc trùng)**
**AI:** Dữ liệu thô từ nhiều nguồn cào khác nhau chắc chắn có trùng lặp. Tôi đã triển khai chiến thuật **"Dual-Key Deduplication"**:
1. **Primary Key (Mã số thuế):** Nếu trùng MST -> Giữ bản ghi đầu tiên, loại bỏ bản ghi sau.
2. **Secondary Key (Hash Tên + Địa chỉ):** Với công ty chưa có MST, tôi tạo hash từ `normalize(name) + normalize(address)`. Nếu trùng hash -> Loại bỏ.
**Result:** File sạch `merged_data_cleaned.jsonl` chứa 1.811.801 bản ghi unique.

**Phase 2: Mapping ITviec Reviews**
**User:** Map review từ file `reviews_itviec.jsonl`. File này có địa chỉ cụ thể nên chắc dễ.
**AI:** Chính xác. Tôi dùng thuật toán khớp `slug_name` (từ URL) và lọc theo Tỉnh/Thành phố.
**Action:** Chạy script `map_itviec_reviews.py`.
**Result:** Map thành công **8,755** công ty. Độ chính xác rất cao nhờ dữ liệu địa chỉ chi tiết.

**Phase 3: Mapping 1900 Reviews (The Challenge)**
**User:** Map tiếp file `reviews_1900.jsonl`. File này tên công ty viết rất ngắn gọn (VD: "CMC Telecom" thay vì "Cong ty TNHH CMC Telecom") và địa chỉ chỉ có Tỉnh.
**Trial 1 (Precise Script - FAILED):**
- **AI Idea:** Dùng Jaccard Similarity và Token matching để bắt các tên viết tắt.
- **Outcome:** Sai lầm nghiêm trọng! Các tên ngắn phổ biến như "Minh Viet", "Thinh Phat" bị map nhầm lung tung (hơn 250,000 matches - quá ảo). Ví dụ: "Thinh Phat" map vào "Hung Thinh Phat".
- **User Feedback:** Kiểm tra thấy sai quá nhiều.

**Trial 2 (Strict Core-Name Script - SUCCESS):**
- **AI Solution:** Quay lại phương pháp cổ điển nhưng chặt chẽ hơn:
  1. **Core Name Extraction:** Loại bỏ triệt để các từ khóa pháp lý (Công ty, TNHH, Group, Invest...).
  2. **Exact Match Only:** Chỉ map khi phần Core Name trùng khớp 100%. Ví dụ: "cmc telecom" == "cmc telecom".
  3. **Geo-Filtering:** Bắt buộc trùng Tỉnh/Thành phố để tránh nhầm chi nhánh.
- **Action:** Chạy script `map_reviews_1900_new.py`.
- **Result:** Kết quả kiểm tra 50 mẫu ngẫu nhiên cho thấy độ chính xác **>95%**. Map đúng các case khó như `Mailisa` (Thẩm mỹ viện vs Công ty), `Freetalk English`...
- **Final Output:** File `data/final_data_full_reviews.jsonl` chứa dữ liệu hoàn chỉnh nhất (Thông tin doanh nghiệp + Reviews từ 2 nguồn).
"""

# Read old content
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        old_content = f.read()
else:
    old_content = "# AI LOG\n"

# Write merged content
if "Phase 1: Deduplication" not in old_content: # Avoid double append
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write(old_content + NEW_CONTENT)
    print("AI Log updated successfully.")
else:
    print("AI Log already contains the update.")
