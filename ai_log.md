# FULL TRANSCRIPT LOG: SEG301 - MILESTONE 1 CRAWLER
## Team: OverFitting
**Date:** 12/01/2026
**Participants:** User (Member 1) & AI Assistant (Antigravity)

---

### [Step 1] Khởi động lại sau phiên trước
**User:** (Yêu cầu tiếp tục Task tối ưu crawler cho Masothue và Thongtindoanhnghiep để đạt 1 triệu records, chi phí 0 đồng).
**Antigravity:**
- Tóm tắt lại tình hình: Đã thử `curl_cffi` bị chặn. Đang chuyển sang Selenium Multi-thread.
- Đề xuất: "Ultimate Hydra Crawler" - Chạy song song nhiều nguồn.

### [Step 2] Triển khai Multi-Threaded Hydra
**Antigravity:** Code xong phiên bản Crawler chạy 2 luồng song song (1 Worker Masothue, 1 Worker Thongtin).
**Action:** Chạy lệnh `LAUNCHING MULTI-THREADED HYDRA...`.
**Status:** 2 cửa sổ Chrome bật lên.

### [Step 3] Lỗi 404 Thongtindoanhnghiep
**User:** "404 rồi" (Kèm ảnh chụp màn hình Chrome báo lỗi trang `thongtindoanhnghiep.co/ha-noi?p=14`).
**Antigravity:**
- Phân tích: URL phân trang bị sai.
- Action: Viết script `debug_url.py` để dò tìm URL đúng (`/page=1`, `/trang-1`...).
- **Result:** Tất cả đều 404 hoặc lỗi kết nối. Nguồn này không ổn định.
- **Quyết định:** Thay thế Thongtindoanhnghiep bằng `Hosocongty.vn`.

### [Step 4] Chuyển đổi sang Hosocongty
**Antigravity:**
- Sửa code `ultimate_crawler.py`: Comment class `ThongtinSource`, bỏ comment `HosocongtySource`.
- Chạy lại Hydra V2.1 (Masothue + Hosocongty).
**User:** (Quan sát log).

### [Step 5] Lỗi Syntax
**User:** "SyntaxError: invalid syntax" (Do file code bị dính ký tự markdown ``` ở cuối).
**Antigravity:**
- Nhận lỗi sơ suất.
- Action: Dùng tool xóa dòng thừa cuối file.
- Action: Chạy lại Hydra V2.1 (Fixed).

### [Step 6] Vấn đề Tốc độ
**User:** "sao dữ liệu cào chậm vậy nhỉ"
**Antigravity:**
- Phân tích: Do phải load trang chi tiết (Detail Page) tốn nhiều thời gian.
- **Chiến lược mới:** "Listing Only" (Chỉ cào trang danh sách, bỏ qua chi tiết nếu đủ thông tin cơ bản).
- Action: Viết script `debug_listing.py` để kiểm tra xem trang danh sách có mã số thuế không.
- Phát hiện: Hosocongty có thông tin ở Listing. Masothue thì không chắc.
- Điều chỉnh: Hosocongty chạy chế độ Listing (Nhanh), Masothue chạy chế độ Detail (Chậm mà chắc).

### [Step 7] Hosocongty Chặn
**User:** "hình như web hócongty không cào được"
**Antigravity:**
- Nghi ngờ selector sai. Viết `debug_hoso.py`.
- **Phát hiện chấn động:** Tiêu đề trang là "Page4Kids - Coloring pages".
- Kết luận: Hosocongty redirect IP của User sang web trẻ em để chống bot.
- **Quyết định:** Bỏ Hosocongty. Chuyển sang `Timcongty.com`.

### [Step 8] Timcongty "No Items"
**User:** "timconty bị no items found"
**Antigravity:**
- Lại nghi ngờ selector. Viết `debug_tim.py`.
- **Phát hiện:** `<body>` chứa `<div id="root">`. Đây là React Single Page App (SPA).
- Phân tích: Không thể cào bằng HTML parser thường vì nội dung render bằng JS sau đó.
- **Kết luận:** Cả 2 nguồn phụ đều "khó ăn".
- **Quyết định lớn:** Quay về nguồn duy nhất **Masothue.com** nhưng chạy **4 Workers** (Swarm Mode).

### [Step 9] Masothue Swarm (4 Workers)
**Antigravity:**
- Refactor code `ultimate_crawler.py`: Xóa hết các nguồn khác. Nhân bản worker Masothue lên 4.
- Chia tải: Worker 1 (Page 1,5,9...), Worker 2 (Page 2,6,10...)...
- Khởi chạy Swarm.

### [Step 10] Câu hỏi Chiến lược
**User:** "chọn web nào chứa đầy đủ thông tin nhất để tập trung cào web đó"
**Antigravity:**
- Đánh giá: **Masothue.com** là đầy đủ và chính xác nhất (Có người đại diện, ngày hoạt động).
- Action: Nâng cấp Parser của Masothue để lấy thêm các trường thông tin này (Rich Data Mode).
- Chạy lại Swarm với code mới.

### [Step 11] Lỗi WinError 183
**User:** Báo lỗi "Cannot create a file when that file already exists..."
**Antigravity:**
- Phân tích: Lỗi Race Condition do 4 Chrome khởi động cùng lúc tranh giành resource.
- Fix: Thêm delay 10s giữa các lần start worker và tạo thư mục profile riêng biệt.
- Kết quả: 4 Workers chạy ổn định.

### [Step 12] Tính toán ETR
**User:** "với tốc độ hiện tại thì bao lâu mới đủ 1.000.000 docs"
**Antigravity:**
- Tính toán: 4.800 docs/giờ -> **208 giờ (8.6 ngày)**.
- User phản hồi: "ok" (nhưng có vẻ vẫn thấy lâu).

### [Step 13] Bị Block Đồng Loạt
**User:** "thấy dữ liệu không tăng nữa"
**Antigravity:**
- Kiểm tra: 4 Workers đều báo "Blocked. Sleep 60s".
- Kết luận: IP đã bị Masothue ban/throttle vì spam 4 luồng.
- **Giải pháp:** Downgrade xuống 1 Worker, chạy "Stealth Mode" (Tàng hình) từ trang 50.

### [Step 14] BƯỚC NGOẶT (PIVOT)
**User:** "Không còn cách nào khác nhanh hơn sao"
**Antigravity:**
- Thừa nhận: Masothue quá khó để cào nhanh IP thường.
- **Ý tưởng:** Tìm "Soft Targets" (Web bảo mật kém).
- Action: Viết `check_targets.py` scan `infodoanhnghiep.com`, `doanhnghiepmoi.vn`, `mst.vn`...
- **BINGO:** `InfoDoanhNghiep.com` phản hồi 200 OK với requests thường. Không WAF.
- **Đề xuất:** Viết `speed_crawler.py` dùng Requests đa luồng (x30) đánh vào InfoDoanhNghiep.

### [Step 15] Speed Crawler V1 & Lỗi 0 items
**Antigravity:** Code và chạy `speed_crawler.py`.
**User:** "sao 0 hết vậy"
**Antigravity:**
- Debug: `debug_selector.py` lấy HTML thật.
- Phát hiện: Sai selector (`.news` vs `.company-item`).
- Fix: Cập nhật selector chuẩn.

### [Step 16] CHIẾN THẮNG
**User:** (Chạy lại V3).
**Kết quả:**
- Log nhảy số liên tục: `[Page 9999] Found 20 items`.
- **Tổng số:** **2.267.964 records**.
- User hỏi: "do code set limit dừng hay hết web?". -> AI: Do set limit an toàn 10k trang, nhưng thế là quá đủ.

### [Step 17] Tổng kết
**User:** Yêu cầu cập nhật `ai_log.md` thật chi tiết, sát với hội thoại.
**Antigravity:** Viết lại bản log này ("Full Transcript Record").

---
**KẾT LUẬN CHUNG:**
Chúng ta đã đi một đường vòng rất lớn:
1. Masothue (Khó) -> 2. Các nguồn phụ (Lỗi/Redirect) -> 3. Masothue 4 Worker (Bị Block) -> 4. **InfoDoanhNghiep (Thành công vĩ đại)**.
Bài học: "Lựa chọn quan trọng hơn nỗ lực".

### [Step 18] Hậu kỳ (Post-Processing) & Clean Data
**User:** Yêu cầu lọc trùng và kiểm tra số lượng thực tế.
**Antigravity:** Code `process_data.py`.
**Kết quả:**
- Tổng Raw: 2.26 triệu records.
- **Unique Tax Code:** 704,170 records.
- **Vấn đề:** Chưa đạt 1.000.000 docs Unique (Do InfoDoanhNghiep phân trang lặp lại nội dung ở các trang cuối).

### [Step 19] FINAL SWEEP (Chiến dịch Vét Cạn)
**User:** Đồng ý mở rộng phạm vi cào.
**Antigravity:**
- Update `speed_crawler.py`: Thêm danh sách **63 Tỉnh Thành** (Thay vì chỉ 12 thành phố lớn).
- Chạy lại với output `speed_data_v2.jsonl`.
- **Mục tiêu:** Thu thập thêm ~300.000 unique records từ các tỉnh lẻ (Thanh Hóa, Nghệ An, Nam Định...) để cán mốc 1 triệu Unique.

**(SESSION CONTINUES - WAITING FOR NATIONWIDE DATA)**

