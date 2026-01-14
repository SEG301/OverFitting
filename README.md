# SEG301 - Vertical Search Engine (Topic 3: Thông tin Doanh nghiệp)

Dự án xây dựng công cụ tìm kiếm doanh nghiệp và đánh giá (Review) quy mô lớn phục vụ môn học SEG301.

## 1. Thành viên nhóm
- [Thành viên 1]
- [Thành viên 2]
- [Thành viên 3]

## 2. Cấu trúc thư mục (Github Structure)
Dự án tuân thủ nghiêm ngặt cấu trúc thư mục yêu cầu:
- `.gitignore`: Bỏ qua dữ liệu lớn và môi trường ảo.
- `README.md`: Hướng dẫn này.
- `ai_log.md`: Nhật ký tương tác với trợ lý AI.
- `requirements.txt`: Các thư viện Python cần thiết.
- `docs/`: Thư mục chứa báo cáo Milestones.
- `data_sample/`: Chứa 100-500 dòng dữ liệu mẫu để kiểm tra.
- `src/`: Mã nguồn chính.
    - `crawler/`: Milestone 1 (spider, parser, utils).
    - `indexer/`: Milestone 2 (Placeholder).
    - `ranking/`: Milestone 2/3 (Placeholder).
    - `ui/`: Milestone 3 (Placeholder).

## 3. Milestone 1: Data Acquisition
Dữ liệu được thu thập từ nguồn **infodoanhnghiep.com** và **1900.com.vn**.

### Kỹ thuật thực hiện:
- **Ngôn ngữ**: Python 3.
- **Thư viện**: `requests`, `BeautifulSoup4` (parser), `pyvi` (Vietnamese Word Segmentation).
- **Đa luồng**: Sử dụng `ThreadPoolExecutor` với 50 workers để tối ưu tốc độ.
- **Cơ chế Resume**: Tự động nhận diện checkpoint từ file dữ liệu đã có để cào tiếp mà không bị trùng.
- **Xử lý trang cuối**: Tự động phát hiện redirect của server để dừng quét trang.

### Cách chạy Crawler:
```bash
# Cài đặt thư viện
pip install -r requirements.txt

# Chạy crawler chính
python -m src.crawler.spider
```

### Dữ liệu:
- **Số lượng**: Mục tiêu 1.000.000 documents.
- **Định dạng**: JSONL (Json Lines).
- **Full Dataset Download**: [Cập nhật link Drive/OneDrive tại đây]

## 4. Nhật ký AI (ai_log.md)
Toàn bộ quá trình giải quyết lỗi, refactor code và tối ưu hóa crawler đều được lưu lại trong `ai_log.md` theo yêu cầu minh bạch của đồ án.
