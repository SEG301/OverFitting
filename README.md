# Đồ án Máy Tìm Kiếm Chuyên Biệt (Vertical Search Engine)
## Chủ đề: Hệ thống tìm kiếm và truy xuất thông tin doanh nghiệp
**Nhóm thực hiện: OverFitting**

---

### 1. Tổng quan dự án
Dự án tập trung xây dựng một máy tìm kiếm chuyên biệt (Vertical Search Engine) quy mô lớn cho dữ liệu doanh nghiệp tại Việt Nam. Hệ thống được thiết kế để xử lý hàng triệu bản ghi, bao gồm toàn bộ quy trình từ thu thập dữ liệu tự động (Crawling), lập chỉ mục (Indexing) đến xếp hạng kết quả tìm kiếm (Ranking).

Dự án này là một phần của môn học **Search Engines & Information Retrieval (SEG301)**.

---

### 2. Cấu trúc thư mục dự án
Kho lưu trữ được tổ chức thành các module riêng biệt nhằm đảm bảo tính bảo trì và khả năng mở rộng:

```text
SEG301-OverFitting/
├── src/                     # Thư mục mã nguồn chính
│   ├── __init__.py
│   └── crawler/             # Milestone 1: Module thu thập và tiền xử lý dữ liệu
│       ├── __init__.py
│       ├── crawl_enterprise.py      # Logic cào dữ liệu doanh nghiệp
│       ├── crawl_reviews_1900.py    # Thu thập review từ 1900.com.vn
│       ├── crawl_reviews_itviec.py  # Thu thập review từ ITviec
│       ├── parser.py                # Phân tích cú pháp HTML
│       ├── process_merge.py         # Gộp dữ liệu và lọc trùng
│       ├── process_map_itviec.py    # Ghép nối review ITviec
│       ├── process_map_1900.py      # Ghép nối review 1900
│       ├── process_segment.py       # Tách từ tiếng Việt cho toàn bộ dữ liệu
│       └── utils.py                 # Các hàm tiện ích chuẩn hóa
├── docs/                    # Tài liệu kỹ thuật và báo cáo
│   └── Milestone1_Report.md # Báo cáo kỹ thuật chi tiết cho Milestone 1
├── data_sample/             # Dữ liệu mẫu để kiểm tra
│   └── sample.jsonl         # Dữ liệu định dạng JSON Lines (100-500 dòng)
├── .gitignore               # Cấu hình loại bỏ môi trường ảo và dữ liệu lớn
├── README.md                # Tài liệu hướng dẫn chính của dự án
├── requirements.txt         # Danh sách các thư viện phụ thuộc
└── ai_log.md                # Nhật ký lịch sử tương tác với trợ lý AI
```

---

### 3. Milestone 1: Thu thập dữ liệu (Data Acquisition)
Mục tiêu trọng tâm của giai đoạn này là xây dựng bộ dữ liệu sạch với quy mô trên **1.000.000 bản ghi**.

#### Chi tiết triển khai kỹ thuật
*   **Thu thập dữ liệu hiệu năng cao**: Sử dụng `ThreadPoolExecutor` với **100 luồng (workers)** song song để tối ưu hóa hiệu suất I/O bound.
*   **Cơ chế Smart Resume**: Hệ thống tự động phân tích các tệp đầu ra hiện có để xác định điểm dừng (checkpoint) cho từng khu vực địa lý, cho phép tiếp tục công việc ngay lập tức sau khi bị gián đoạn.
*   **Xử lý phân trang thông minh**: Tự động nhận diện cơ chế "Soft Redirect" từ phía máy chủ để xác định chính xác điểm kết thúc của luồng dữ liệu.
*   **Trích xuất dữ liệu chuyên sâu**:
    *   Trích xuất Mã số thuế, Người đại diện và Danh sách ngành nghề chi tiết bằng Regex và các bộ chọn BeautifulSoup nâng cao.
    *   **Tách từ tiếng Việt (Word Segmentation)**: Tích hợp thư viện `PyVi` để thực hiện tách từ tiếng Việt, một bước chuẩn bị bắt buộc cho giai đoạn lập chỉ mục.
*   **Loại bỏ trùng lặp (Deduplication)**: Quản lý trạng thái toàn cục để đảm bảo tính duy nhất dựa trên bộ khóa kết hợp: Mã số thuế, Tên công ty và Địa chỉ.

#### Thống kê dữ liệu
*   **Nguồn dữ liệu**: `infodoanhnghiep.com`
*   **Tổng số lượng**: **1.848.043** tài liệu duy nhất.
*   **Định dạng lưu trữ**: JSONL (JSON Lines) giúp tối ưu dung lượng và tốc độ xử lý.
*   **Tổng dung lượng**: Khoảng 6.1 GB (File cuối cùng đã tách từ toàn bộ).

---

### 4. Hướng dẫn cài đặt và Sử dụng

#### Thiết lập môi trường
Yêu cầu Python phiên bản 3.9 trở lên.

```bash
# Tải mã nguồn từ repository
git clone https://github.com/SEG301/OverFitting.git
cd SEG301-OverFitting

# Khởi tạo môi trường ảo
python -m venv venv

# Kích hoạt trên Windows:
venv\Scripts\activate
# Kích hoạt trên macOS/Linux:
source venv/bin/activate

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

#### Thực thi Crawler
Trình thu thập dữ liệu doanh nghiệp chính:
```bash
python -m src.crawler.crawl_enterprise
```

---

### 5. Truy cập dữ liệu (Dataset)
Do giới hạn kích thước tệp của GitHub, bộ dữ liệu đầy đủ (1.8 triệu bản ghi) được lưu trữ tại:
*   [Dữ liệu đầy đủ Milestone 1 - Google Drive](https://drive.google.com/drive/folders/1XdAX7aw-ibpCniuHVyMNmUkD9JHv-dK-?usp=sharing)
*   Dữ liệu mẫu (200 bản ghi) có sẵn tại thư mục: `data_sample/sample.jsonl`.

---

### 6. Nhật ký tương tác AI (AI Interaction Log)
Tuân thủ chính sách **Zero Tolerance Policy** của môn học, tệp `ai_log.md` ghi lại toàn bộ quá trình trao đổi với các công cụ AI. Các nội dung chính bao gồm:
*   Tối ưu hóa quản lý luồng và kết nối (Thread pool & Connection management).
*   Xử lý các vòng lặp phân trang dư thừa.
*   Tái cấu trúc mã nguồn (Refactoring) để tăng tính module hóa.

---

### 7. Lộ trình dự án (Roadmap)
*   **Milestone 2**: Triển khai thuật toán lập chỉ mục **SPIMI** và thuật toán xếp hạng **BM25**.
*   **Milestone 3**: Tích hợp khả năng tìm kiếm ngữ nghĩa (**Vector Search**) và phát triển giao diện người dùng trên nền tảng web.

---
**Nhóm OverFitting - 2026**
