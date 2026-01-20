# Hướng dẫn phân chia công việc - Team 3 người
## SEG301 - Milestone 1: Data Acquisition

---

## 🎯 Mục tiêu: 1.000.000 documents

| Thành viên | Nguồn | Ước tính | Trạng thái |
|------------|-------|----------|------------|
| **Member 1** | Masothue (Ngành 1-25) | ~350,000 | ⏳ |
| **Member 2** | Masothue (Ngành 26-73) | ~450,000 | ⏳ |
| **Member 3** | Hosocongty + Reviewcongty | ~200,000 | ⏳ |

---

## 📋 Hướng dẫn cài đặt (Mỗi thành viên đều làm)

### 1. Clone repository
```bash
git clone https://github.com/SEG301/OverFitting.git
cd OverFitting
```

### 2. Tạo Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

### 4. Test cài đặt
```bash
python -c "from src.crawler import MasothueCrawler; print('OK')"
```

---

## 👤 Member 1: Masothue - Ngành 1-25

### Chạy crawler
```bash
# Chạy full (sẽ mất 1-2 ngày)
python -m src.crawler.main crawl --source masothue --industries 1-25 --output data_member1

# Hoặc test trước với limit
python -m src.crawler.main crawl --source masothue --industries 1-25 --limit 1000 --output data_member1
```

### Resume nếu bị gián đoạn
```bash
python -m src.crawler.main crawl --source masothue --industries 1-25 --output data_member1 --resume
```

### Kiểm tra tiến độ
- File checkpoint: `data_member1/masothue_checkpoint.json`
- Xem log: `crawler.log`

---

## 👤 Member 2: Masothue - Ngành 26-73

### Chạy crawler
```bash
# Chạy full
python -m src.crawler.main crawl --source masothue --industries 26-73 --output data_member2

# Test trước
python -m src.crawler.main crawl --source masothue --industries 26-73 --limit 1000 --output data_member2
```

---

## 👤 Member 3: Hosocongty + Reviewcongty

### Chạy crawler
```bash
# Chạy Hosocongty
python3 -m src.crawler.main crawl --source hosocongty --output data_member3

# Chạy Reviewcongty
python3 -m src.crawler.main crawl --source reviewcongty --output data_member3
```

---

## 🔄 Sau khi crawl xong - Merge dữ liệu

### 1. Thu thập files từ các thành viên
Mỗi người upload folder `data_memberX/` lên Google Drive hoặc copy sang máy leader.

### 2. Merge tất cả dữ liệu
```bash
# Gộp tất cả file JSONL
python -m src.crawler.main merge \
    --masothue "data_member1/*.jsonl" "data_member2/*.jsonl" \
    --hosocongty "data_member3/hosocongty*.jsonl" \
    --reviewcongty "data_member3/reviewcongty*.jsonl" \
    --output data/all_companies_merged.jsonl
```

### 3. Loại bỏ trùng lặp
```bash
python -m src.crawler.main dedup \
    --input "data/all_companies_merged.jsonl" \
    --output "data/all_companies_final.jsonl" \
    --key tax_code
```

### 4. Tạo thống kê
```bash
python -m src.crawler.main stats \
    --input "data/all_companies_final.jsonl" \
    --output "docs/data_statistics.md"
```

---

## 📊 Checklist trước khi nộp

### Về dữ liệu
- [ ] Đủ 1.000.000 documents
- [ ] Không có duplicate (đã chạy dedup)
- [ ] Text đã được segment (có field `_segmented`)
- [ ] File lưu dạng JSONL

### Về code
- [ ] Có xử lý async/multi-thread ✅
- [ ] Có cơ chế resume (checkpoint) ✅
- [ ] Code module hóa (nhiều file) ✅

### Về GitHub
- [ ] Commit đều đặn (mỗi ngày ít nhất 1 commit)
- [ ] `ai_log.md` được cập nhật
- [ ] `README.md` có link tải dataset

### Về báo cáo
- [ ] `docs/Milestone1_Report.pdf`
- [ ] Thống kê số lượng từ vựng
- [ ] Độ dài trung bình documents

---

## ⚠️ Lưu ý quan trọng

1. **KHÔNG upload file dữ liệu lên GitHub** - File 1 triệu dòng quá lớn!
2. **Upload dữ liệu lên Google Drive** và để link trong README
3. **Commit code thường xuyên** - Yêu cầu bắt buộc của môn!
4. **Cập nhật ai_log.md** mỗi khi chat với AI

---

## 🆘 Troubleshooting

### Bị block IP
```bash
# Giảm concurrent requests
python3 -m src.crawler.main crawl --source masothue --concurrent 10

# Hoặc tăng rate limit (chậm hơn)
python3 -m src.crawler.main crawl --source masothue --delay 2.0
```

### Lỗi RAM không đủ
- Đóng các ứng dụng khác
- Giảm `max_concurrent` xuống 20

### Resume không hoạt động
- Kiểm tra file checkpoint có tồn tại không
- Xóa checkpoint để crawl lại từ đầu:
```bash
rm data_memberX/*_checkpoint.json
```
