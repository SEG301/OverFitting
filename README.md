# SEG301 - ENTERPRISE DATA CRAWLER
**Team:** OverFitting
**Milestone:** 1 (Data Acquisition)

## 🚀 Overview
Project này chứa các công cụ thu thập dữ liệu doanh nghiệp Việt Nam từ các nguồn công khai.
Mục tiêu: Thu thập >1.000.000 bản ghi doanh nghiệp (Tên, MST, Địa chỉ...).

## 📂 Structure
- `src/crawler/speed_crawler.py`: **(RECOMMENDED)** Crawler tốc độ cao (Requests + Multi-threading), nhắm vào `infodoanhnghiep.com`. Tốc độ ~1000 docs/s.
- `src/crawler/ultimate_crawler.py`: Crawler dự phòng (Selenium + Undetected Chromedriver) để vượt WAF (Cloudflare) của `masothue.com`.

## 🛠 Installation
1. Clone repo:
```bash
git clone https://github.com/SEG301/OverFitting.git
cd SEG301-OverFitting
```

2. Setup Virtual Environment (Windows):
```powershell
python -m venv venv
.\venv\Scripts\activate
```

3. Install Dependencies:
```bash
pip install -r requirements.txt
```

## ⚡ Usage
### 1. Fast Crawling (Recommended)
Để thu thập dữ liệu nhanh (Milestone 1):
```bash
python src/crawler/speed_crawler.py
```
- Dữ liệu sẽ lưu tại: `data_member1/speed_data.jsonl`
- Tốc độ dự kiến: 1 Phút ~ 50.000 records.

### 2. Deep Crawling (Use with caution)
Để thu thập dữ liệu chi tiết từ nguồn khó (Masothue):
```bash
python src/crawler/ultimate_crawler.py
```
*(Lưu ý: Chỉ chạy 1 worker để tránh bị khóa IP)*

## 📊 Results (Milestone 1)
- **Total Records:** 2,267,000+
- **Format:** JSON Lines (.jsonl)
- **Fields:** `company_name`, `tax_code`, `address`, `source`, `url`.

---
*Developed by Team OverFitting @ 2026*
