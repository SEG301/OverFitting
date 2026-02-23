# SEG301 - SEARCH ENGINES & INFORMATION RETRIEVAL

## Project: Vietnamese Enterprise Search Engine

## Nhóm thực hiện: OverFitting

### 👥 Thành viên nhóm

1. **Nguyễn Thanh Trà** - QE190099
2. **Phan Đỗ Thanh Tuấn** - QE190123
3. **Châu Thái Nhật Minh** - QE190109

---

### 📝 1. Tổng quan & Mục tiêu

Dự án tập trung xây dựng một **Vertical Search Engine** (Máy tìm kiếm chuyên biệt) cho chủ đề **Thông tin Doanh nghiệp & Review**. Dự án kéo dài qua 3 giai đoạn:

- **Milestone 1**: Thu thập, làm sạch và làm giàu bộ dữ liệu doanh nghiệp (> 1.8 triệu dòng).
- **Milestone 2**: Xây dựng hệ thống lập chỉ mục (SPIMI) và xếp hạng (BM25) hiệu năng cao.
- **Milestone 3**: (Upcoming) Vector Search, Giao diện Web & Hybrid Search.

---

### 📂 2. Cấu trúc thư mục dự án

Hệ thống được tổ chức module hóa theo từng giai đoạn:

```text
SEG301-OverFitting/
├── src/                     # Source code chính
│   ├── crawler/             # Milestone 1: Thu thập & Tiền xử lý
│   │   ├── crawl_enterprise.py      # Crawler đa luồng hiệu năng cao
│   │   ├── crawl_reviews.py         # Cào dữ liệu review (ITviec, 1900)
│   │   ├── run_pipeline.py          # Pipeline nối, sạch và tách từ (M1)
│   │   └── parser.py                # Logic bóc tách HTML chuyên sâu
│   ├── indexer/             # Milestone 2: Lập chỉ mục SPIMI
│   │   ├── spimi.py         # Indexing theo blocks để tối ưu RAM
│   │   ├── merging.py       # K-way merge các blocks thành Inverted Index
│   │   └── compression.py   # (Mới) Kỹ thuật nén VByte & Delta
│   ├── ranking/             # Milestone 2: Xếp hạng BM25
│   │   └── bm25.py          # Thuật toán BM25 (code tay, tối ưu Random Access)
│   └── search_console.py    # Console App tìm kiếm tương tác
├── tests/                   # Unit tests đảm bảo tính đúng đắn thuật toán
├── docs/                    # Thư mục báo cáo & tài liệu
│   └── Milestone1_Report.md # Báo cáo chi tiết giai đoạn 1
├── data/                    # Dữ liệu dự án (bị gitignore)
│   ├── milestone1_fixed.jsonl
│   └── index/               # Thư mục chứa Inverted Index files
├── requirements.txt         # Các thư viện cần thiết
├── .gitignore               # Cấu hình Git
├── ai_log.md                # Nhật ký tương tác AI (Bắt buộc)
└── README.md                # Hướng dẫn này
```

---

### 🛠️ 3. Chi tiết triển khai & Điểm nổi bật

#### 🔹 Milestone 1: Data Acquisition & Enrichment

- **Hiệu năng cao**: ThreadPool 50 luồng, xử lý ~1000 cty/phút.
- **Security Bypass**: Giả lập TLS Fingerprint (Chrome 120) vượt rào cản Cloudflare/WAF.
- **Làm sạch chuyên sâu**: Title Case cho tên/địa chỉ, tách từ dính, chuẩn hóa Unicode.
- **Tách từ (Segmentation)**: Sử dụng `PyVi` để tối ưu dữ liệu tiếng Việt.
- **Thống kê M1**:
  - **1.842.525 documents** sạch.
  - ~6.2 GB dữ liệu JSONL.
  - [Link tải full dataset (M1)](https://drive.google.com/drive/folders/1XdAX7aw-ibpCniuHVyMNmUkD9JHv-dK-?usp=sharing)

#### 🔹 Milestone 2: Core Search Engine (SPIMI + BM25)

- **Thuật toán SPIMI**: Xây dựng Inverted Index theo từng block 50k docs, tránh tràn RAM.
- **Xếp hạng BM25**: Triển khai thủ công 100% công thức BM25 (IDF, TF Saturation, Length Normalization).
- **Kiến trúc Index 2-File**:
  - `term_dict.pkl` (~18MB): Load cực nhanh vào RAM.
  - `postings.bin` (~1GB): Đọc danh sách postings qua cơ chế **File Seek (O(1))**.
- **Siêu tối ưu RAM**: Sử dụng Byte Offsets để đọc Metadata thông tin công ty từ JSONL gốc khi cần hiển thị.
- **Hiệu năng M2**:
  - **RAM tiêu thụ**: ~55 MB (giảm từ 3GB+).
  - **Khởi động**: < 1.0 giây.
  - **Tìm kiếm**: < 0.1 giây / truy vấn.

---

### 💻 4. Hướng dẫn chạy dự án

#### Bước 1: Khởi tạo môi trường

```bash
python -m venv venv
source venv/bin/activate  # Hoặc venv\Scripts\activate trên Windows
pip install -r requirements.txt
```

#### Bước 2: Milestone 1 - Thu thập & Xử lý (Nếu cần)

```bash
python src/crawler/run_pipeline.py
```

#### Bước 3: Milestone 2 - Lập chỉ mục & Tìm kiếm

```bash
# Xây dựng Inverted Index
python src/indexer/spimi.py
python src/indexer/merging.py

# Chạy Console Search
python src/search_console.py
```

---

### 🛡️ 5. Zero Tolerance Policy & AI Log

- **GitHub**: Commit lịch sử minh bạch cho mọi thay đổi.
- **AI Log**: Mọi quá trình hỗ trợ từ AI được ghi nhận tại `ai_log.md`, bao gồm cả các giai đoạn debug thuật toán và tối ưu memory.

---
Nhóm OverFitting - 2026
