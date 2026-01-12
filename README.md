# SEG301 - PROJECT MILESTONE 1
**Topic:** Business Information Retrieval
**Group:** OverFitting

## Project Overview
This project implements a high-performance web crawler to acquire business registration data from public sources. The goal is to collect, clean, and standardize over 1,000,000 business records for building a Vertical Search Engine.

## Data Acquisition Statistics
- **Source:** InfoDoanhNghiep
- **Total Raw Records:** 8,177,481
- **Total Unique Records:** 1,298,633 (De-duplicated by Tax Code & Name)
- **Vocabulary Size:** 393,194 words
- **Average Document Length:** 19.24 words

## 💾 Dataset Download
Do dung lượng dữ liệu lớn (>800MB), chúng tôi lưu trữ Full Dataset trên Google Drive.

👉 **Download Link:** [Full Dataset Milestone 1 (Google Drive)](https://drive.google.com/drive/folders/1XdAX7aw-ibpCniuHVyMNmUkD9JHv-dK-?usp=sharing)

*File mẫu xem trước trên Github:* `data_sample/sample.jsonl` (50 records).

## Repository Structure
```
SEG301-OverFitting/
├── .gitignore               # Git configuration
├── README.md                # Project documentation
├── ai_log.md                # AI Interaction Log (Audit trail)
├── requirements.txt         # Python dependencies
├── docs/                    # Documentation & Reports
│   └── Milestone1_Report.md
├── data_sample/             # Data samples for grading
│   └── sample.jsonl         # Sample dataset
└── src/                     # Source Code
    └── crawler/
        ├── speed_crawler.py # Multi-threaded Crawler
        └── final_process.py # Data Cleaning Pipeline
```

## Setup & Usage

### Prerequisites
- Python 3.10+
- Recommended: Visual Studio Code

### Installation
1. Clone the repository.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Crawler
To start the acquisition process (Nationwide sweep):
```bash
python src/crawler/speed_crawler.py
```
*Note: The crawler uses 30 concurrent threads. Ensure stable network connection.*

### Data Processing
To merge, de-duplicate, and segment words:
```bash
python src/crawler/final_process.py
```
Output will be saved to `data/milestone1_final.jsonl` (Local only, not git-tracked).

## Data Format (JSONL)
Each line in the dataset represents a unique business record:
```json
{
  "company_name": "CÔNG TY TNHH VÍ DỤ",
  "tax_code": "0101234567",
  "address": "Số 1, Đường A, Quận B, TP. Hà Nội",
  "source": "InfoDoanhNghiep",
  "url": "https://infodoanhnghiep.com/...",
  "company_name_seg": "CÔNG_TY TNHH VÍ_DỤ",
  "address_seg": "Số 1 , Đường A , Quận B , TP . Hà_Nội"
}
```

---
**Course:** SEG301 - Search Engines & Information Retrieval
**Mileage:** Milestone 1 (Week 4)
