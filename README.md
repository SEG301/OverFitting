# SEG301 - SEARCH ENGINES & INFORMATION RETRIEVAL

## Milestone 1: Data Acquisition (20%)

## Nhóm thực hiện: OverFitting

### 👥 Thành viên nhóm

1. **Nguyễn Thanh Trà** - QE190099
2. **Phan Đỗ Thanh Tuấn** - QE190123
3. **Châu Thái Nhật Minh** - QE190109

---

### 📝 1. Tổng quan & Mục tiêu

Dự án tập trung xây dựng một **Vertical Search Engine** (Máy tìm kiếm chuyên biệt) cho chủ đề **Thông tin Doanh nghiệp & Review**.

- **Mục tiêu chính**: Xây dựng bộ dữ liệu sạch tối thiểu **1.000.000 documents**.
- **Nguồn dữ liệu**: infodoanhnghiep.com, itviec.com, 1900.com.vn.
- **Công nghệ**: Python, High-performance Multi-threading, NLP (Word Segmentation).

---

### 📂 2. Cấu trúc thư mục dự án

Hệ thống được tổ chức theo module hóa nghiêm ngặt theo yêu cầu môn học:

```text
SEG301-OverFitting/
├── src/                     # Source code chính
│   ├── __init__.py
│   └── crawler/             # Milestone 1: Code thu thập & xử lý
│       ├── crawl_enterprise.py      # Cào dữ liệu gốc từ InfoDoanhNghiep
│       ├── crawl_reviews.py         # Cào dữ liệu review từ ITviec & 1900
│       ├── step1_mapping.py         # Khớp review vào dữ liệu doanh nghiệp
│       ├── step2_deduplicate.py     # Loại bỏ trùng lặp (Dual-Key)
│       ├── step3_cleaning.py        # Làm sạch (HTML, Title Case, Fix lỗi font)
│       ├── step4_segmentation.py    # Tách từ tiếng Việt (Word Segmentation)
│       ├── run_pipeline.py          # File thực thi toàn bộ luồng xử lý
│       ├── parser.py                # Logic bóc tách HTML chuyên sâu
│       └── utils.py                 # Hàm tiện ích chuẩn hóa
├── docs/                    # Thư mục báo cáo & tài liệu
│   └── Milestone1_Report.md # Báo cáo chi tiết Milestone 1
├── data_sample/             # Dữ liệu mẫu (100 docs)
│   └── sample.jsonl
├── requirements.txt         # Các thư viện cần thiết (pip install -r ...)
├── .gitignore               # Cấu hình bỏ qua rác và dữ liệu lớn
├── ai_log.md                # Nhật ký sử dụng AI (Bắt buộc)
└── README.md                # Hướng dẫn này
```

---

### 🛠️ 3. Kỹ thuật triển khai & Điểm nổi bật

- **Hiệu năng cao**: Sử dụng `ThreadPoolExecutor` với **100 luồng** song song, tối ưu hóa tốc độ I/O bound.

- **Anti-Bot & Security Bypass**: Tích hợp `curl_cffi` để giả lập TLS Fingerprint của trình duyệt Chrome 120, vượt qua các rào cản từ Cloudflare/WAF.
- **Cơ chế Tự động Phục hồi (Checkpoint)**: Duy trì trạng thái cào theo thời gian thực, cho phép tiếp tục công việc ngay lập tức sau sự cố.
- **Quy trình Tiền xử lý Dữ liệu**:
  - **Làm sạch (Cleaning)**: Chuẩn hóa Case, loại bỏ mã HTML dư thừa và fix lỗi giải mã Unicode.
  - **Khử trùng lặp (Deduplication)**: Áp dụng cơ chế lọc trùng thông minh (Dual-Key) dựa trên Mã số thuế và định danh thực thể.
  - **Liên kết (Mapping)**: Khớp nối đánh giá (Reviews) từ nhiều nguồn vào đúng pháp nhân doanh nghiệp.
  - **Tách từ (Segmentation)**: Tối ưu hóa dữ liệu tiếng Việt bằng thư viện `PyVi` (đạt tốc độ ~140.000 dòng/phút).

---

### 📊 4. Thống kê bộ dữ liệu

- **Tổng số lượng**: **1.842.525 documents** (Vượt mức 1 triệu yêu cầu).

- **Dung lượng**: ~6.1 GB (Dữ liệu sạch, đã tách từ).
- **Định dạng**: JSON Lines (.jsonl).
- **Link tải full dataset**: [Google Drive Link](https://drive.google.com/drive/folders/1XdAX7aw-ibpCniuHVyMNmUkD9JHv-dK-?usp=sharing)

---

### 💻 5. Hướng dẫn cài đặt & Chạy dự án

#### Bước 1: Khởi tạo môi trường

```bash
# Clone repository
git clone https://github.com/SEG301/OverFitting.git
cd SEG301-OverFitting

# Tạo và kích hoạt môi trường ảo
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Cài đặt thư viện
pip install -r requirements.txt
```

#### Bước 2: Chạy crawler (Nếu cần thu thêm dữ liệu)

```bash
python src/crawler/crawl_enterprise.py
python src/crawler/crawl_reviews.py
```

#### Bước 3: Chạy Pipeline xử lý dữ liệu sạch

File này sẽ tự động chạy từ Step 1 đến Step 4:

```bash
python src/crawler/run_pipeline.py
```

---

### 🛡️ 6. Zero Tolerance Policy & AI Log

Chúng tôi tuân thủ tuyệt đối quy định của môn học:

- **GitHub**: Lịch sử commit đều đặn, rõ ràng từng tính năng.
- **AI Log**: Toàn bộ quá trình trao đổi với AI được ghi lại trung thực tại `ai_log.md`.
- **Author Verification**: Sẵn sàng giải thích mọi dòng code cho giảng viên khi vấn đáp.

---
Nhóm OverFitting - 2026
