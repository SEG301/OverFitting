# AI INTERACTION LOG
## Team: OverFitting

---

## Date: 2026-01-11

### Task 1: Khởi tạo dự án Milestone 1 - Data Acquisition

**User:** Dựa vào file đặc tả SEG301, giúp tôi hoàn thành milestone 1 - chủ đề 3 (Thông tin Doanh nghiệp) theo cách tối ưu nhất.

**AI (Claude):** Tôi đã phân tích yêu cầu và tạo kế hoạch triển khai:

1. **Cấu trúc dự án**: Theo đúng template GitHub yêu cầu
2. **Nguồn dữ liệu**: 
   - Masothue.com (~800K docs)
   - Hosocongty.vn (~150K docs) 
   - Reviewcongty.com (~50K docs)
3. **Kỹ thuật crawl**: 
   - Async với aiohttp
   - Checkpoint system để resume
   - Rate limiting tránh bị block
4. **Phân chia team 3 người**:
   - TV1: Masothue (Hà Nội + DN mới)
   - TV2: Masothue (TP.HCM + các tỉnh)
   - TV3: Hosocongty + Reviewcongty

---

### Task 2: Tạo cấu trúc project

**User:** Tạo project với tên SEG301-OverFitting

**AI:** Đã tạo các file:
- `.gitignore` - Loại bỏ venv, data lớn, __pycache__
- `README.md` - Hướng dẫn cài đặt và sử dụng
- `TEAM_GUIDE.md` - Phân chia công việc cho 3 người
- `requirements.txt` - Dependencies (aiohttp, beautifulsoup4, underthesea, etc.)
- `src/crawler/base_crawler.py` - AsyncCrawler base class
- `src/crawler/masothue_crawler.py` - Crawler cho masothue.com
- `src/crawler/hosocongty_crawler.py` - Crawler cho hosocongty.vn
- `src/crawler/reviewcongty_crawler.py` - Crawler cho reviewcongty.com
- `src/crawler/parser.py` - HTML cleaning + Vietnamese word segmentation
- `src/crawler/utils.py` - Deduplication, JSONL I/O, statistics
- `src/crawler/main.py` - CLI entry point

---

### Task 3: Push lên GitHub

**User:** Push lên https://github.com/SEG301/OverFitting.git

**AI:** Đã push thành công với commit:
```
Initial commit: Milestone 1 - Data Acquisition setup
- Complete project structure following SEG301 requirements
- AsyncCrawler base class with checkpoint/resume support
- Crawlers for Masothue, Hosocongty, Reviewcongty
- Vietnamese word segmentation with Underthesea
```

---

### Task 4: Member 1 bắt đầu crawl

**User:** Tôi là Member 1, thực hiện nhiệm vụ của tôi

**AI:** 
1. Đầu tiên thử crawl bằng script gốc → bị rate limit (HTTP 429)
2. Phân tích cấu trúc masothue.com bằng browser:
   - Tìm được trang "Doanh nghiệp mới": `/tra-cuu-ma-so-thue-doanh-nghiep-moi-thanh-lap`
   - Tìm được trang theo tỉnh: `/tra-cuu-ma-so-thue-theo-tinh/ha-noi-1`
   - Pagination: `?page=N`
3. Tạo `member1_crawl.py` - Script tối ưu:
   - Crawl từ listing pages (không đoán mã số thuế)
   - Rate limit 2-4 giây/request
   - Checkpoint tự động mỗi 50 items
   - Resume khi bị gián đoạn

**Kết quả test:** Crawl thành công 20 companies với đầy đủ thông tin:
- tax_code, company_name, address, industry, registration_date
- Word segmentation hoạt động tốt

---

### Task 5: Giải thích cơ chế Resume

**User:** Nếu tắt ứng dụng giữa chừng thì hôm sau sẽ crawl tiếp hay crawl lại?

**AI:** **SẼ CRAWL TIẾP, KHÔNG CRAWL LẠI.**

Cơ chế:
1. Crawler lưu `checkpoint_member1.json` mỗi 50 items
2. Checkpoint chứa danh sách URLs đã crawl
3. Khi chạy lại, đọc checkpoint và skip những URLs đã có

Cách sử dụng:
```powershell
# Chạy lần đầu hoặc tiếp tục
.\venv\Scripts\python.exe member1_crawl.py

# Kiểm tra số lượng đã crawl
(Get-Content data_member1\masothue_member1.jsonl | Measure-Object -Line).Lines
```

---

*[Tiếp tục cập nhật...]*

