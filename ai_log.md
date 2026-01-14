# AI INTERACTION LOG - SEG301 Project

## Date: 2026-01-10
**Task:** Khởi tạo đồ án và lựa chọn công nghệ cho Crawler Milestone 1.

**User:** Tôi cần xây dựng crawler cho chủ đề Thông tin doanh nghiệp (Topic 3). Bạn đề xuất công cụ nào?
**AI:** Theo cấu trúc đồ án và yêu cầu về hiệu năng, bạn nên dùng `requests` và `BeautifulSoup` kết hợp với `ThreadPoolExecutor` (đa luồng). Nếu gặp trang dùng JavaScript mạnh có thể dùng thêm `Selenium`.
**Result:** Khởi tạo các file crawler cơ bản đầu tiên.

## Date: 2026-01-12
**Task:** Xử lý anti-bot và cào dữ liệu Review.

**User:** Trang 1900.com.vn có dữ liệu review rất tốt, hãy cào chi tiết Ưu/Nhược điểm.
**AI:** Đã phân tích DOM của 1900.com.vn. Selector cho Ưu điểm là `strong.greenColor` và Nhược điểm là `strong.text-danger`. Đã viết script `crawler_1900_detailed.py` để lấy data này.
**Result:** Thu thập được khoảng 10,000 comment chi tiết có rating và tag.

## Date: 2026-01-13
**Task:** Tối ưu hóa Crawler Doanh nghiệp và Modular hóa mã nguồn (Milestone 1).

**User:** Crawler đang chạy trên infodoanhnghiep.com bị lỗi không dừng khi hết trang. Hãy kiểm tra và tối ưu tốc độ.
**AI:** 
1. **Lỗi Pagination**: Phát hiện server thực hiện redirect về trang chủ region khi số trang vượt quá giới hạn (thay vì 404). Đã thêm logic kiểm tra URL redirect (`if "trang-" not in resp.url`) để dừng crawler chính xác.
2. **Hiệu năng**: Tăng số lượng worker lên 50. Tốc độ đạt ~10k docs/phút.
3. **Cấu trúc (Refactor)**: 
   - Tái cấu trúc file `speed_crawler.py` thành các module `spider.py`, `parser.py`, và `utils.py` để tuân thủ yêu cầu module hóa của đồ án.
   - `spider.py`: Logic quản lý luồng và resume.
   - `parser.py`: Logic bóc tách HTML và tách từ tiếng Việt (Word Segmentation).
   - `utils.py`: Các hàm tiện ích dùng chung.
4. **Data Sample**: Tạo file `sample.jsonl` chứa 100 bản ghi thực tế trong thư mục `data_sample/`.

**User:** Đẩy code lên Github và cập nhật báo cáo.
**AI:** Đã hoàn thiện cấu trúc thư mục, cập nhật README.md hướng dẫn cài đặt và báo cáo Milestone 1. Tiến hành đẩy mã nguồn lên Github tại https://github.com/SEG301/OverFitting.git.
**Result:** Project hoàn thiện Milestone 1, đúng spec, code sạch và hiệu năng cao.

---
*Ghi chú: Toàn bộ quá trình chat được lưu tự động để giảng viên đối chiếu tính trung thực của mã nguồn.*
