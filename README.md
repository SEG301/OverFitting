# SEG301 - Search Engine & Information Retrieval
## Team: OverFitting

### Chủ đề: Thông tin Doanh nghiệp Việt Nam
Xây dựng Vertical Search Engine cho dữ liệu doanh nghiệp từ nhiều nguồn:
- **Masothue.com** - Thông tin mã số thuế, địa chỉ, ngành nghề
- **Hosocongty.vn** - Hồ sơ doanh nghiệp chi tiết
- **Reviewcongty.com** - Đánh giá từ nhân viên

---

## 📥 Dataset
> **Full Dataset (1M+ documents):** [Google Drive Link - Coming Soon]

Sample data: `data_sample/sample.jsonl` (500 docs)

---

## 🚀 Cài đặt

```bash
# Clone repo
git clone https://github.com/SEG301/OverFitting.git
cd OverFitting

# Tạo virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Cài đặt dependencies
pip install -r requirements.txt
```

---

## 📊 Chạy Crawler (Milestone 1)

### Crawl sample (100 docs)
```bash
python -m src.crawler.main --source masothue --limit 100
```

### Crawl đầy đủ (cho từng thành viên)
```bash
# Thành viên 1: Masothue + Ngành 1-25
python -m src.crawler.main --source masothue --industries 1-25

# Thành viên 2: Masothue + Ngành 26-50
python -m src.crawler.main --source masothue --industries 26-50

# Thành viên 3: Hosocongty + Reviewcongty
python -m src.crawler.main --source hosocongty reviewcongty
```

### Resume khi bị gián đoạn
```bash
python3 -m src.crawler.main --resume
```

---

## 📁 Cấu trúc thư mục

```
SEG301-OverFitting/
├── .gitignore
├── README.md
├── ai_log.md              # Nhật ký AI
├── requirements.txt
├── docs/
│   ├── Milestone1_Report.pdf
│   ├── Milestone2_Report.pdf
│   └── Milestone3_Presentation.pdf
├── data_sample/
│   └── sample.jsonl       # 500 docs mẫu
├── src/
│   ├── __init__.py
│   ├── crawler/           # Milestone 1
│   │   ├── __init__.py
│   │   ├── base_crawler.py
│   │   ├── masothue_crawler.py
│   │   ├── hosocongty_crawler.py
│   │   ├── reviewcongty_crawler.py
│   │   ├── parser.py
│   │   ├── utils.py
│   │   └── main.py
│   ├── indexer/           # Milestone 2
│   │   ├── __init__.py
│   │   ├── spimi.py
│   │   ├── merging.py
│   │   └── compression.py
│   ├── ranking/           # Milestone 2 & 3
│   │   ├── __init__.py
│   │   ├── bm25.py
│   │   └── vector.py
│   └── ui/                # Milestone 3
│       └── app.py
└── tests/
    ├── test_crawler.py
    ├── test_spimi.py
    └── test_bm25.py
```

---

## 👥 Team Members
| Thành viên | MSSV | Phân công |
|------------|------|-----------|
| Member 1 | | Masothue (ngành 1-25) |
| Member 2 | | Masothue (ngành 26-50+) |
| Member 3 | | Hosocongty + Reviewcongty |

---

## 📈 Progress

### Milestone 1: Data Acquisition (20%)
- [ ] Crawl 1,000,000 documents
- [ ] Clean & segment data
- [ ] Statistics report

### Milestone 2: Core Search Engine (20%)
- [ ] SPIMI Indexing
- [ ] BM25 Ranking
- [ ] Console App

### Milestone 3: Final Product (20%)
- [ ] Vector Search
- [ ] Web Interface
- [ ] Evaluation
