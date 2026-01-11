# AI INTERACTION LOG
## Team: OverFitting

---

## Date: 2026-01-11

### Task: Khởi tạo dự án Milestone 1 - Data Acquisition

**User:** Dựa vào file đặc tả SEG301, giúp tôi hoàn thành milestone 1 - chủ đề 3 (Thông tin Doanh nghiệp) theo cách tối ưu nhất.

**AI (Claude):** Tôi đã phân tích yêu cầu và tạo kế hoạch triển khai:

1. **Cấu trúc dự án**: Theo đúng template GitHub yêu cầu
2. **Nguồn dữ liệu**: 
   - Masothue.com (~800K docs)
   - Hosocongty.vn (~150K docs) 
   - Reviewcongty.com (~50K docs)
3. **Kỹ thuật crawl**: 
   - Async với aiohttp (100 concurrent)
   - Checkpoint system để resume
   - Rate limiting tránh bị block
4. **Phân chia team 3 người**:
   - TV1: Masothue ngành 1-25
   - TV2: Masothue ngành 26-50+
   - TV3: Hosocongty + Reviewcongty

---

### Task: Viết base_crawler.py

**User:** Tiếp tục implement code crawler

**AI:** [Code được generate - xem file src/crawler/base_crawler.py]

Giải thích các điểm quan trọng:
- `AsyncCrawler` class với semaphore để limit concurrent requests
- `save_checkpoint()` và `load_checkpoint()` cho resume capability
- Exponential backoff khi gặp error
- User-agent rotation với fake-useragent

---

*[Tiếp tục cập nhật theo tiến độ làm việc...]*
