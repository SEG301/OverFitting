# BÁO CÁO MILESTONE 1: THU THẬP DỮ LIỆU (DATA ACQUISITION)

## 1. Thông tin chung
- **Chủ đề**: Thông tin Doanh nghiệp (Topic 3).
- **Mục tiêu**: Thu thập tối thiểu 1.000.000 documents sạch, đã được tách từ tiếng Việt.
- **Kết quả thực tế**: Đã thu thu thập được **1.848.043** documents (Vượt 84% so với chỉ tiêu).
- **Dung lượng file**: ~1.02 GB (.jsonl).

## 2. Nguồn dữ liệu
- **infodoanhnghiep.com**: Nguồn dữ liệu chính cho thông tin doanh nghiệp (Tên, MST, Địa chỉ).

## 3. Quy trình kỹ thuật
### 3.1. Crawling ( spider.py )
- **Kỹ thuật**: `requests` + `BeautifulSoup4`.
- **Đa luồng**: Triển khai `ThreadPoolExecutor` với **50 workers**.
- **Cơ chế Resume**: Kiểm tra dữ liệu đã có trong file JSONL để nạp vào bộ nhớ trước khi cào, giúp tránh trùng lặp khi khởi động lại.
- **Xử lý Pagination**: Phát hiện cơ chế redirect của server khi hết trang (Soft Redirect) để dừng crawler đúng lúc, tránh vòng lặp vô tận.

### 3.2. Cleaning & Word Segmentation ( parser.py )
- **Deduplication**: Lọc trùng dựa trên bộ khóa `(tax_code, company_name)`.
- **Word Segmentation (Tách từ)**: Sử dụng thư viện `PyVi` để thực hiện tách từ tiếng Việt.

## 4. Tại sao cần Word Segmentation (Tách từ)?
Trong tiếng Việt, khoảng trắng không phải lúc nào cũng ngăn cách các từ đơn lẻ (ví dụ: "Sách giáo khoa" là 1 từ ghép nhưng có 2 khoảng trắng).
- **Tăng độ chính xác (Precision)**: Giúp máy tìm kiếm hiểu "Công ty" là một thực thể chứ không phải hai từ "Công" và "ty" riêng lẻ.
- **Tối ưu hóa Index**: Khi thực hiện Milestone 2 (Indexing), việc lưu trữ các từ đã tách (`cong_ty`, `tnhh`) giúp thuật toán tìm kiếm (BM25) hoạt động hiệu quả hơn, trả về kết quả sát với ngữ nghĩa của người dùng nhất.
- **Yêu cầu đồ án**: Đây là tiêu chí bắt buộc để đánh giá chất lượng xử lý dữ liệu của Milestone 1.

## 5. Cấu trúc thư mục Github
Dự án được tổ chức module hóa theo yêu cầu:
- `src/crawler/spider.py`: Quản lý luồng và điều hướng.
- `src/crawler/parser.py`: Trích xuất dữ liệu và tách từ.
- `src/crawler/utils.py`: Các hàm tiện ích chuẩn hóa văn bản.
- `data_sample/sample.jsonl`: Chứa 100 bản ghi mẫu.
