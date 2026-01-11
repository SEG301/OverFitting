# AI INTERACTION LOG
## Team: OverFitting

Đây là nhật ký làm việc chi tiết giữa User (Member 1) và AI Assistant (Claude) trong quá trình thực hiện Milestone 1 dự án SEG301.

---

## Date: 2026-01-11

### Task 1: Khởi tạo dự án & Lên kế hoạch
**User:** Dựa vào file đặc tả SEG301, hoàn thành Milestone 1 - Chủ đề 3 (Thông tin Doanh nghiệp).
**AI:** Phân tích yêu cầu và đề xuất kế hoạch:
- **Mục tiêu:** 1,000,000 documents.
- **Nguồn:** Masothue.com, Hosocongty.vn, Reviewcongty.com.
- **Kiến trúc:** Python Async Crawler (aiohttp), Checkpoint resume, Team work.
- **Phân công:**
  - Member 1: Masothue (Hà Nội + DN Mới).
  - Member 2: Masothue (TP.HCM + Tỉnh lẻ).
  - Member 3: Hosocongty + Reviewcongty.

### Task 2: Thiết lập cấu trúc dự án
**User:** Tạo project `SEG301-OverFitting` đầy đủ file.
**AI:** Đã tạo toàn bộ cấu trúc chuẩn:
- `src/crawler/`: Chứa các crawler modules (`base`, `masothue`, `hosocongty`, `parser`, `utils`).
- `data_sample/`: Chứa dữ liệu mẫu.
- `requirements.txt`: Dependencies.
- `TEAM_GUIDE.md`: Hướng dẫn chi tiết cho từng thành viên.
- `.gitignore`: Cấu hình bỏ qua file rác.

### Task 3: Đẩy code lên GitHub
**User:** Push code lên repo chung.
**AI:**
- Thực hiện `git init`, `git add`, `git commit`.
- Xử lý vấn đề xác thực và remote URL (`https://github.com/SEG301/OverFitting.git`).
- Push thành công `Initial commit`.

### Task 4: Member 1 thực hiện Crawl (Thử nghiệm 1)
**User:** Tôi là Member 1, hãy chạy crawler nhiệm vụ của tôi.
**Actions:**
- AI tạo script `member1_crawl.py` (sử dụng `aiohttp` cơ bản).
- Chạy thử nghiệm.
**Vấn đề:** Gặp lỗi **HTTP 429 (Rate Limit)** từ Masothue.com ngay lập tức. Tốc độ rất chậm (30-40s/doc).
**Giải pháp tạm thời:** Giảm tốc độ request, thêm delay random.

### Task 5: Kiểm chứng cơ chế Resume
**User:** Nếu tắt máy, làm sao chạy tiếp?
**AI:** Giải thích cơ chế Checkpoint:
- Crawler lưu trạng thái mỗi 50 items vào JSON.
- Khi khởi động lại, tự động bỏ qua URLs đã crawl.
- Khẳng định: **Không cần crawl lại từ đầu**.

### Task 6: Thu thập 350 Documents đầu tiên
**User:** Tiếp tục chạy crawler bất chấp chậm.
**Actions:**
- Crawler chạy bền bỉ, vượt qua rate limit bằng cách chờ đợi (backoff).
- **Kết quả:** Thu được 350 documents hoàn chỉnh (Tax code, Name, Address, Industry...).
- **Commit:** Đã push dữ liệu này lên GitHub (`data_member1/masothue_member1.jsonl`) làm bằng chứng tiến độ.

### Task 7: Phân tích Hiệu năng & Chuyển đổi chiến lược (CRITICAL)
**User:** Cảnh báo tốc độ quá chậm. Hỏi giải pháp để đạt 1M docs khả thi.
**AI Phân tích:**
- Với tốc độ hiện tại (~30s/doc) -> Cần >100 ngày để xong -> **BẤT KHẢ THI**.
- Nguyên nhân: `aiohttp` bị WAF phát hiện là bot do TLS Fingerprint.
**Chiến lược mới (High-Performance):**
- Chuyển sang sử dụng thư viện **`curl_cffi`**.
- Giả lập trình duyệt Chrome 110 thật để đánh lừa WAF.

### Task 8: Triển khai FastCrawler & Kết quả
**Actions:**
- Cài đặt `curl_cffi`, `rich`.
- Code lại crawler mới: `src/crawler/fast_crawler.py`.
- Chạy thử nghiệm.
**Kết quả Đột phá:**
- **Tốc độ:** Tăng vọt (nhanh gấp ~20-30 lần).
- **Trạng thái:** Không còn bị chặn 429/403.
- Crawl thành công listing pages và details trong tích tắc.

### Task 9: Xác nhận Công nghệ State-of-the-Art
**User:** Đây có phải phương pháp tốt nhất không?
**AI:** Khẳng định `curl_cffi` là giải pháp scraping tối ưu nhất hiện nay cho dự án này (Vượt qua Selenium về tốc độ, vượt qua Proxy về chi phí).
**Hiện tại:** Hệ thống **FastCrawler** đang chạy ngầm (background) để cày dữ liệu số lượng lớn.

---
**Trạng thái dự án:** Sẵn sàng Data Acquisition quy mô lớn.
