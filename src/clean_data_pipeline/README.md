# Clean Data Pipeline

Pipeline xử lý và làm sạch dữ liệu thô thành dữ liệu chuẩn cho Search Engine.

## Quy trình (theo thứ tự)

```
merged_raw_3_sources.jsonl (Input ~1.85M records)
        |
        v
[01_deduplicate.py]     -> 01_deduplicated.jsonl    (Lọc trùng TRƯỚC)
        |
        v
[02_fix_errors.py]      -> 02_cleaned.jsonl         (Clean data)
        |
        v
[03_map_itviec.py]      -> 03_with_itviec.jsonl     (Map ITviec reviews)
        |
        v
[04_map_1900.py]        -> 04_with_all_reviews.jsonl (Map 1900 reviews)
        |
        v
[05_segment.py]         -> 05_final_segmented.jsonl  (Output cuối)
```

## Chi tiết từng bước

| Step | File | Chức năng |
|------|------|-----------|
| 1 | `01_deduplicate.py` | Lọc trùng theo 3 trường: Tax + Name + Address |
| 2 | `02_fix_errors.py` | Clean toàn diện: |
|   |                    | - Company Name: Fix ALL CAPS, ký tự lỗi |
|   |                    | - Representative: Xóa digits, fix ALL CAPS |
|   |                    | - Address: Tách từ dính, chuẩn hóa Case |
| 3 | `03_map_itviec.py` | Map review từ `reviews_itviec.jsonl` |
| 4 | `04_map_1900.py` | Map review từ `reviews_1900_detailed.jsonl` |
| 5 | `05_segment.py` | Tách từ PyVi, **CHỈ segment review Tiếng Việt** |

## Cách chạy

```bash
cd e:\Crwal\OverFitting

python src/clean_data_pipeline/01_deduplicate.py
python src/clean_data_pipeline/02_fix_errors.py
python src/clean_data_pipeline/03_map_itviec.py
python src/clean_data_pipeline/04_map_1900.py
python src/clean_data_pipeline/05_segment.py
```

## Yêu cầu

```bash
pip install pyvi
```

## Kết quả

File: `data/05_final_segmented.jsonl`
- ~1.8M+ bản ghi
- Sạch, đã chuẩn hóa
- Review tiếng Anh giữ nguyên
