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
│   │   └── merging.py       # K-way merge các blocks thành Inverted Index
│   ├── ranking/             # Milestone 2: Xếp hạng BM25
│   │   └── bm25.py          # BM25 + Coordination Boost (mã nguồn cốt lõi)
│   └── search_console.py    # Console App tìm kiếm tương tác
├── support/                 # Công cụ kiểm chứng & Thống kê
│   └── index_stats_verifier.py # Script kiểm tra Index Statistics thực tế
├── tests/                   # Unit tests đảm bảo tính đúng đắn thuật toán
├── docs/                    # Thư mục báo cáo & tài liệu
│   ├── Milestone1_Report.md # Báo cáo chi tiết giai đoạn 1
│   └── Milestone2_Report.md # Báo cáo chi tiết giai đoạn 2 (Mới)
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
  - [Link tải full dataset (M1)](https://drive.google.com/drive/folders/1XdAX7aw-ibpCniuHVyMNmUkD9JHv-dK-?usp=sharing)

#### 🔹 Milestone 2: Core Search Engine (SPIMI + BM25)

- **Thuật toán SPIMI**: Xây dựng Inverted Index theo từng block 50k docs, tránh tràn RAM.
- **BM25 & Coordination Boost**:
  - Triển khai thủ công 100% công thức BM25.
  - **Coordination Factor**: Tăng điểm cho kết quả khớp đồng thời nhiều từ khóa (tăng Precision).
- **Kiến trúc Index 2-File**:
  - `term_dict.pkl` (~18MB): Lưu 695k từ vựng duy nhất.
  - `postings.bin` (~1GB): Đọc postings qua cơ chế **File Seek (O(1))**.
- **Siêu tối ưu RAM & Hiển thị**:
  - **Metadata On-demand**: Chỉ đọc thông tin công ty từ JSONL khi cần hiển thị (RAM < 60MB).
  - **Metadata Fallback**: Tự động khôi phục thông tin Industry bị thiếu từ nhiều nguồn dữ liệu thô.
- **Thống kê M2 thực tế**:
  - **Vocabulary**: 695,470 terms.
  - **Total Tokens**: 342,502,541.
  - **Search Time**: < 0.5 giây (đã tối ưu Hot-loop).

---

### 💻 4. Hướng dẫn chạy dự án

#### Bước 1: Khởi tạo môi trường

```bash
python -m venv venv
source venv/bin/activate  # Hoặc venv\Scripts\activate trên Windows
pip install -r requirements.txt
```

#### Bước 2: Milestone 2 - Lập chỉ mục & Kiểm chứng

```bash
# 1. Xây dựng Inverted Index (SPIMI)
python src/indexer/spimi.py
python src/indexer/merging.py

# 2. Kiểm chứng số liệu thống kê thực tế
python support/index_stats_verifier.py
```

#### Bước 3: Tìm kiếm tương tác

```bash
# Chạy Console Search
python src/search_console.py
```

---

### 🛡️ 5. Zero Tolerance Policy & AI Log

- **GitHub History**: Commit rõ ràng, chia nhỏ module thay vì upload 1 lần.
- **AI Interaction Log**: Chi tiết tại `ai_log.md` (bao gồm lịch sử tối ưu thuật toán & debug RAM).

---
Nhóm OverFitting - 2026
