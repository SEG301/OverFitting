# BÁO CÁO MILESTONE 1: THU THẬP DỮ LIỆU (DATA ACQUISITION)

## 1. Thông tin chung
- **Chủ đề**: Thông tin Doanh nghiệp & Đánh giá (Topic 3).
- **Mục tiêu**: Thu thập 1.000.000 documents sạch, đã được tách từ tiếng Việt.

## 2. Nguồn dữ liệu
1. **infodoanhnghiep.com**: Cung cấp thông tin nền tảng (Tên, MST, Địa chỉ).
2. **1900.com.vn**: Cung cấp dữ liệu đánh giá (Reviews) chi tiết (Ưu điểm, nhược điểm, rating).

## 3. Quy trình kỹ thuật
### 3.1. Crawling ( spider.py )
- **Kỹ thuật**: `requests` + `BeautifulSoup4`.
- **Hiệu năng**: Triển khai đa luồng (`ThreadPoolExecutor`) với **50 workers**.
- **Cơ chế Resume**: Crawler lưu checkpoint vào file JSONL, khi chạy lại sẽ tự động bỏ qua các bản ghi đã tồn tại.
- **Xử lý Pagination**: Tự động nhận diện redirect khi vượt quá số trang cho phép của server để dừng quét chính xác.

### 3.2. Cleaning ( parser.py )
- **Regex**: Trích xuất chính xác Mã số thuế và Địa chỉ từ các khối văn bản thô.
- **Deduplication**: Lọc trùng lặp ngay trong quá trình cào dựa trên `tax_code` và `company_name`.
- **Word Segmentation**: Sử dụng thư viện `PyVi` để tách từ tiếng Việt cho trường `company_name_seg` và `address_seg`.

## 4. Thống kê dữ liệu
- **Tổng số bản ghi**: ~15,000+ (đang tiếp tục cào).
- **Định dạng**: JSONL.
- **Chất lượng**: 100% bản ghi có Mã số thuế hợp lệ, không lỗi font UTF-8.

## 5. Cấu trúc thư mục Github
Đã tổ chức dự án theo đúng chuẩn yêu cầu:
- `src/crawler/`: Chứa toàn bộ mã nguồn thu thập dữ liệu.
- `data_sample/`: Chứa file mẫu `sample.jsonl`.
- `ai_log.md`: Nhật ký sử dụng AI minh bạch.
