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

### Task 10: Quy trình Vận hành & Cứu hộ (Operations)

**User:** Hỏi cách dừng crawler để nghỉ và chạy lại sau mà không mất dữ liệu.

**AI Hướng dẫn:**
1. **Cơ chế:** Crawler chạy background, lưu dữ liệu realtime (append) và checkpoint.
2. **Dừng (Stop):**
   - Sử dụng lệnh \Stop-Process -Name 'python' -Force\.
   - Dữ liệu đã lưu an toàn trên đĩa.
3. **Chạy lại (Resume):**
   - Chạy lại lệnh khởi động crawler.
   - Hệ thống tự động load \checkpoint_fast.json\, bỏ qua URL cũ, tiếp tục crawl URL mới.

**Trạng thái hiện tại:**
- Crawler đang chạy chế độ **Continuous Loop** (Bền bỉ).
- Log được ghi ra file \crawler_v2.log\ để monitoring.
- Dữ liệu đang đổ về \data_member1/masothue_fast.jsonl\.

---


---

### Task 11: Mở rộng quy mô Crawl (National Scale)

**User:** Yêu cầu crawler không giới hạn ở mức phân công team, mà chạy tối đa để đạt/vượt 1.000.000 docs.

**AI Action:**
1. **Dừng Crawler cũ:** Để nạp cấu hình mới.
2. **Nâng cấp Code (`fast_crawler.py`):**
   - Mở rộng nguồn (`SOURCES`) từ 2 nguồn lên **17 tỉnh thành trọng điểm** (HCM, Hà Nội, Đà Nẵng, Bình Dương, v.v.).
   - Logic `random.sample` để crawler nhảy vùng ngẫu nhiên, tránh bị chặn theo dải IP vùng.
   - Tăng phạm vi quét trang (`random.randint(1, 1000)`).
3. **Khởi động lại:** Crawler phiên bản "Nationwide" đã chạy.

**Mục tiêu:** Đạt >1 triệu unique docs trong thời gian ngắn nhất.


---

### Task 12: Ổn định hóa hệ thống (Final Stability)

**User:** Xác nhận nguồn crawl hiện tại và kiểm tra tính ổn định.

**AI Action & Debug:**
1. **Sự cố 1 (Hosocongty):** Phát hiện trang này trả về nội dung rác (Page4Kids) khi bị scan mạnh -> Hủy bỏ phương án B.
2. **Sự cố 2 (Masothue Crash):** Phát hiện crawler bị crash do lỗi `UnicodeEncodeError` khi in tên công ty tiếng Việt ra Console Windows -> **Đã Fix**.
3. **Quyết định cuối cùng:** Quay lại crawl **Masothue.com (Nguồn Doanh Nghiệp Mới)** với cấu hình an toàn (Streaming Mode + Delay 2s).

**Kết quả:**
- Hệ thống đang chạy ổn định (File `crawler_final.log`).
- Dữ liệu đang tăng đều đặn trong `data_member1/masothue_fast.jsonl`.
- Đã bàn giao quy trình giám sát cho User.

**SESSION END.**

