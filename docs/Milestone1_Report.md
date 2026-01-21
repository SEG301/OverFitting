# BÁO CÁO MILESTONE 1: THU THẬP DỮ LIỆU (DATA ACQUISITION)

## 1. Thông tin chung
- **Chủ đề**: Thông tin Doanh nghiệp (Topic 3).
- **Mục tiêu**: Thu thập tối thiểu 1.000.000 documents sạch, đã được tách từ tiếng Việt.
- **Kết quả thực tế**: Đã thu thu thập được **1.848.043** documents (Vượt 84% so với chỉ tiêu đề ra).
- **Dung lượng file**: ~6.1 GB (File đã qua xử lý tách từ toàn bộ).
- **Định dạng**: JSON Lines (.jsonl).

---

## 2. Nguồn dữ liệu
Để đảm bảo tính đa dạng và chất lượng thông tin, nhóm đã khai thác 3 nguồn dữ liệu chính:
1. **infodoanhnghiep.com**: Nguồn dữ liệu gốc về pháp nhân doanh nghiệp, mã số thuế và ngành nghề kinh doanh.
2. **itviec.com**: Nguồn đánh giá (reviews) chất lượng cao từ nhân viên và ứng viên.
3. **1900.com.vn**: Nguồn đánh giá bổ sung về trải nghiệm làm việc và môi trường doanh nghiệp.

Dữ liệu thu thập bao gồm:
- **Thông tin cơ bản**: Tên công ty, Mã số thuế, Địa chỉ, Người đại diện.
- **Dữ liệu chuyên sâu**: Tình trạng hoạt động, Ngành nghề kinh doanh đầy đủ (Mã ngành + Tên ngành).
- **Trải nghiệm người dùng**: Danh sách các reviews kèm tiêu đề, nội dung và đánh giá sao.

---

## 3. Quy trình kỹ thuật (Pipeline)
Hệ thống được thiết kế theo dạng module hóa, chia thành các công đoạn độc lập:

### 3.1. Crawling (Thu thập)
- **Công cụ**: `requests` + `BeautifulSoup4` + `curl_cffi`.
- **Hiệu năng**: Triển khai **100 luồng (workers)** song song, đạt tốc độ ~1.200 - 1.500 requests/phút.
- **Scripts**: 
    - `crawl_enterprise.py`: Cào dữ liệu doanh nghiệp.
    - `crawl_reviews_itviec.py`: Cào reviews từ ITviec.
    - `crawl_reviews_1900.py`: Cào reviews từ 1900.com.vn.

### 3.2. Processing (Xử lý & Gộp)
- **Gộp dữ liệu (`process_merge.py`)**: Kết hợp các file JSONL từ nhiều nguồn, loại bỏ trùng lặp dựa trên khóa định danh `(tax_code, company_name, address)`.
- **Mapping Review (`process_map_*.py`)**: Sử dụng thuật toán so khớp tên lõi (Core-name matching) và lọc theo địa lý (Province matching) để gắn chính xác review vào từng doanh nghiệp.

### 3.3. Enrichment & Tokenization (`process_segment.py`)
- **Tách từ tiếng Việt**: Sử dụng thư viện `PyVi` (ViTokenizer) để xử lý toàn bộ dữ liệu.
- **Đối tượng xử lý**: Tách từ cho Tên công ty, Địa chỉ, Người đại diện, Ngành nghề và Nội dung review.

---

## 4. Insight & Thống kê dữ liệu (Data Statistics)
Dựa trên việc phân tích mẫu 50.000 bản ghi từ bộ dữ liệu cuối cùng, nhóm trích xuất được các chỉ số quan trọng sau:

| Chỉ số thống kê | Giá trị |
| :--- | :--- |
| **Tổng số lượng bản ghi (Unique)** | 1.848.043 |
| **Kích thước từ vựng (Vocabulary Size)** | ~57.589 từ |
| **Độ dài trung bình mỗi tài liệu** | ~275.24 tokens |
| **Số lượng reviews đã khớp nối** | >10.000 reviews |

**Nhận xét**: 
- Độ dài trung bình tài liệu khá lớn (~275 tokens) cho thấy dữ liệu có độ sâu thông tin rất tốt (bao gồm nhiều ngành nghề và đánh giá chi tiết).
- Kích thước từ vựng (~57k từ) phản ánh sự phong phú của thuật ngữ chuyên ngành kinh tế và từ ngữ tự nhiên trong reviews.

---

## 5. Tại sao cần Word Segmentation (Tách từ)?
Trong tiếng Việt, khoảng trắng không phải lúc nào cũng ngăn cách các từ đơn lẻ.
- **Tăng độ chính xác (Precision)**: Giúp máy tìm kiếm hiểu "Công ty" là một thực thể chứ không phải hai từ "Công" và "ty" riêng lẻ.
- **Tối ưu hóa Index**: Khi thực hiện Milestone 2 (Indexing), việc lưu trữ các từ đã tách (`cong_ty`, `tnhh`) giúp thuật toán tìm kiếm (BM25) hoạt động hiệu quả hơn.

---

## 6. Cấu trúc thư mục mã nguồn
Dự án tuân thủ nghiêm ngặt quy định tổ chức của môn học:
- `src/crawler/`: Chứa tất cả script thu thập và tiền xử lý.
- `docs/`: Chứa báo cáo Milestone.
- `data_sample/`: Chứa file mẫu `sample.jsonl` (đã tách từ).
- `ai_log.md`: Nhật ký tương tác AI (Tuân thủ Zero Tolerance Policy).

---
**Nhóm OverFitting - 1/2026**
