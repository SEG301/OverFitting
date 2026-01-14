# SEG301 - Vertical Search Engine (Topic 3: Thông tin Doanh nghiệp & Review)

Dự án xây dựng công cụ tìm kiếm và phân tích dữ liệu doanh nghiệp quy mô lớn phục vụ môn học Search Engines & Information Retrieval (SEG301).

## 1. Thành viên nhóm - Project Group
- **Nhóm**: OverFitting

## 2. Cấu trúc thư mục (Github Structure)
Dự án được tổ chức theo module hóa để đảm bảo khả năng mở rộng và bảo trì:
- `.gitignore`: Cấu hình bỏ qua môi trường ảo (`venv`), các file rác và dữ liệu lớn (`data/`).
- `README.md`: Hướng dẫn cài đặt, sử dụng và thông tin dataset.
- `ai_log.md`: Nhật ký tương tác chi tiết với trợ lý AI (Lịch sử giải quyết lỗi, tối ưu crawler).
- `requirements.txt`: Danh sách các thư viện cần thiết.
- `docs/`: Chứa các báo cáo kỹ thuật cho từng Milestone.
- `data_sample/`: Chứa dữ liệu mẫu (100-500 dòng) để giảng viên kiểm tra nhanh cấu trúc dữ liệu.
- `src/`: Mã nguồn chính của dự án.
    - `crawler/`: Milestone 1 - Thu thập dữ liệu (Spider, Parser, Utils).
    - `indexer/`: Milestone 2 - Tạo chỉ mục (Placeholder).
    - `ranking/`: Milestone 2/3 - Xếp hạng & Tìm kiếm (Placeholder).
    - `ui/`: Milestone 3 - Giao diện người dùng (Placeholder).

## 3. Milestone 1: Data Acquisition (Thu thập dữ liệu)
Chúng tôi đã xây dựng hệ thống cào dữ liệu hiệu năng cao cho hơn 63 tỉnh thành tại Việt Nam.

### Kỹ thuật sử dụng:
- **Đa luồng (Multi-threading)**: Sử dụng `ThreadPoolExecutor` với **50 workers** giúp tối ưu hóa băng thông mạng.
- **Cơ chế Sweeping**: Quét dữ liệu theo Batch (50 trang/lần) để duy trì tốc độ ổn định.
- **Cơ chế Resume**: Tự động nhận diện checkpoint từ dữ liệu đã cào để tiếp tục công việc khi bị gián đoạn.
- **Xử lý Pagination**: Bổ sung logic nhận diện Redirect để dừng crawler chính xác khi hết trang (Soft Redirect Detection).
- **Làm sạch dữ liệu & Tách từ**:
    - Trích xuất MST, Tên, Địa chỉ bằng Regex.
    - Lọc trùng theo bộ khóa `(Tax_Code, Company_Name, Address)`.
    - Tách từ tiếng Việt bằng thư viện `PyVi`.

### Cách chạy Crawler:
```bash
# 1. Cài đặt môi trường
pip install -r requirements.txt

# 2. Chạy crawler chính (Quét 63 tỉnh thành)
python -m src.crawler.spider
# Hoặc sử dụng shortcut:
python src/crawler/speed_crawler.py
```

## 4. Dữ liệu (Dataset)
- **Tổng số lượng bản ghi**: **1.848.043** documents.
- **Định dạng**: JSONL (Json Lines).
- **Link tải Full Dataset**: [Google Drive - Full Data Milestone 1](https://drive.google.com/drive/folders/1XdAX7aw-ibpCniuHVyMNmUkD9JHv-dK-?usp=sharing)
- **Mẫu dữ liệu**: Xem tại `data_sample/sample.jsonl`.

## 5. Nhật ký AI (ai_log.md)
File `ai_log.md` ghi lại chi tiết toàn bộ quá trình trao đổi với AI, bao gồm các bước:
- Chuyển đổi công nghệ từ Selenium (Masothue) sang Requests (Infodoanhnghiep).
- Cách cấu hình đa luồng để vượt mốc 1 triệu bản ghi.
- Logic gỡ lỗi Infinite Pagination Loop.
- Quá trình Refactor mã nguồn thành dạng Module.
