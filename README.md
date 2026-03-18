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
- **Web Framework**: `FastAPI` (Backend) + HTML/CSS/JS thuần (Frontend), thay thế dự định dùng Streamlit ban đầu để đạt hiệu suất và tính tuỳ biến giao diện tối đa.

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
│   ├── ranking/             # Milestone 2 & 3: Xếp hạng & AI Search
│   │   ├── bm25.py          # BM25 + Coordination Boost (code tay 100%)
│   │   ├── vector.py        # Vector Search dùng FAISS + Sentence-Transformers (M3)
│   │   └── hybrid.py        # Hybrid Search: RRF kết hợp BM25 + Vector (M3)
│   ├── ui/                  # Milestone 3: Giao diện người dùng
│   │   └── app.py           # Streamlit Web App
│   └── search_console.py    # Console App tìm kiếm tương tác (M2)
├── tests/                   # Unit tests & Evaluation
│   ├── test_spimi.py
│   ├── test_bm25.py
│   └── evaluate.py          # Đánh giá P@10 cho 20 queries (M3)
├── docs/                    # Thư mục báo cáo & tài liệu
│   ├── Milestone1_Report.md
│   ├── Milestone2_Report.md
│   └── Milestone3_Report.md # Báo cáo Milestone 3 (Mới)
├── data/                    # Dữ liệu dự án (bị gitignore)
│   ├── milestone1_fixed.jsonl
│   └── index/               # Inverted Index + FAISS Vector Index
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

#### 🔹 Milestone 3: AI Integration & Final Product

- **Vector Search (Semantic AI)**:
  - Model: `paraphrase-multilingual-MiniLM-L12-v2` (hỗ trợ Tiếng Việt).
  - Tối đa hoá ngữ nghĩa: Vector được encode từ chuỗi **5 trường thông tin** liên kết (Tên, Ngành nghề, Địa chỉ, Đại diện, Trạng thái). Xử lý hàng loạt 1.8M bản ghi bằng phần cứng GPU (CUDA).
- **Hybrid Search (RRF) & Rule-based Boosts**:
  - Kết hợp BM25 (Lexical) + Vector Search (Semantic) bằng **Reciprocal Rank Fusion** (`alpha = 0.65`).
  - Tích hợp **Exact Match & Substring Boost**: Thuật toán tự thưởng điểm khổng lồ (20.0 - 100.0 điểm) để ghim Top 1 cho các truy vấn khớp mặt chữ tuyệt đối, hoặc khớp một đoạn (Substring) Tên công ty / Địa chỉ cụ thể.
  - Tích hợp **MST Bypass Scan**: Tra cứu bằng Mã số thuế sẽ bỏ qua Vector/BM25, khởi động luồng quét Text-Scan cực nhanh (`O(N)` trong ~200ms) đảm bảo chính xác tuyệt đối 100%.
- **Ranking Core Optimization (BM25 Tuning)**:
  - Tái thiết kế phương trình Coordination Factor: Zero-penalty đối với các câu truy vấn chứa Stop-words (từ chối skip-word bug).
  - Hạ chuẩn Document Length `B=0.4` triệt tiêu lợi thế xếp hạng của các Name-Spam ngắn.
- **Web Interface (FastAPI + Vanilla UI)**:
  - Kiến trúc Front-end sạch, vô hiệu hoá Emojis, UX mô phỏng Google Search. Khóa cuộn Modal nền (`overflow: hidden`).
  - Cơ chế **Static Load-more Pagination**: Frontend nhận 500-1000 kết quả từ API nhưng chỉ render 10 DOM elements, load thêm tức thì `0s` delay.
  - **Dynamic Province Filter**: Thuật toán JS tự động bóc tách Địa chỉ (chuẩn hoá tiền tố Tỉnh/TP) để đẻ ra các Option tương ứng cấu thành Dropdown lọc Tuỳ Biến thông minh.
- **Evaluation**:
  - So sánh Precision@10 giữa BM25, Vector Search và Hybrid Search. Kết quả Hybrid System cực kỳ hiệu quả, đáp ứng mọi truy vấn khó.


---

### 💻 4. Hướng dẫn chạy dự án

#### Bước 1: Khởi tạo môi trường

```bash
python -m venv venv
source venv/bin/activate  # Hoặc venv\Scripts\activate trên Windows
pip install -r requirements.txt
```

#### Bước 2: Milestone 2 - Lập chỉ mục & Tìm kiếm

```bash
# Xây dựng Inverted Index (SPIMI)
python src/indexer/spimi.py
python src/indexer/merging.py
```

#### Bước 3: Milestone 3 - AI Vector & FastAPI Server

```bash
# Tạo Vector Index (FAISS)
python src/ranking/vector.py

# Chạy Web UI (FastAPI)
python src/ui/server.py
```

#### Bước 4: Tìm kiếm dòng lệnh (Console)

```bash
python src/search_console.py
```

---

### 🛡️ 5. Zero Tolerance Policy & AI Log

- **GitHub History**: Commit rõ ràng, chia nhỏ module thay vì upload 1 lần.
- **AI Interaction Log**: Chi tiết tại `ai_log.md` (bao gồm lịch sử tối ưu thuật toán & debug RAM).

---
Nhóm OverFitting - 2026
