# BÁO CÁO KỸ THUẬT MILESTONE 2: INDEXING & RANKING

**Môn học**: Search Engines & Information Retrieval (SEG301)  
**Nhóm thực hiện**: OverFitting  
**Chủ đề**: Vertical Search Engine cho Thông tin Doanh nghiệp & Reviews

---

## 1. Thông tin thành viên

* **Nguyễn Thanh Trà** - QE190099
* **Phan Đỗ Thanh Tuấn** - QE190123
* **Châu Thái Nhật Minh** - QE190109

---

## 2. Mục tiêu Milestone 2

Xây dựng hệ thống tìm kiếm toàn văn (Full-text Search) mạnh mẽ, có khả năng xử lý hàng triệu bản ghi với tài nguyên RAM hạn chế. Tập trung vào:

* **Indexing**: Triển khai thuật toán SPIMI (Single-Pass In-Memory Indexing).
* **Ranking**: Sử dụng thuật toán BM25 (Best Matching 25) kết hợp các tùy chỉnh thực tế.
* **Optimization**: Tối ưu hóa bộ nhớ và tốc độ tìm kiếm.

---

## 3. Kiến trúc Đánh chỉ mục (Indexing)

Hệ thống sử dụng bộ mã nguồn nằm trong thư mục `src/indexer/` để chuyển đổi dữ liệu thô thành cấu trúc tìm kiếm.

### 3.1. Thuật toán SPIMI (`spimi.py` & `merging.py`)

Nhóm triển khai thuật toán SPIMI để giải quyết bài toán tràn bộ nhớ khi xử lý 1.8 triệu bản ghi:

* **Giai đoạn 1 (`spimi.py`)**: Đọc dữ liệu JSONL, chia thành từng khối 50,000 tài liệu. Mỗi khối được đánh chỉ mục trong RAM và ghi xuống đĩa dưới dạng các file blocks tạm thời.
* **Giai đoạn 2 (`merging.py`)**: Sử dụng cấu trúc Min-heap (`heapq`) để gộp (merge) các block con thành một Inverted Index duy nhất, sắp xếp theo thứ tự alphabet để tối ưu tốc độ truy vấn.

### 3.2. Cấu trúc Index 2-File (Memory-Efficient Architecture)

Để đạt tốc độ search nhanh mà không tốn RAM, bộ chỉ mục trong `data/index/` được thiết kế tách biệt:

1. **`term_dict.pkl` (~18 MB)**: Từ điển (Vocabulary) lưu mapping từ khóa sang vị trí byte (offset) và độ dài trong file postings. Chỉ file này được load vào RAM khi khởi động.
2. **`postings.bin` (~1.04 GB)**: Lưu danh sách postings (doc_id, tf) dưới dạng nhị phân. Dữ liệu được đọc trực tiếp từ đĩa thông qua `f.seek()`, giúp RAM tiêu thụ cực thấp (~55 MB).

---

## 4. Thuật toán Xếp hạng (Ranking)

Toàn bộ logic xếp hạng được đóng gói trong tệp **`src/ranking/bm25.py`**.

### 4.1. Cốt lõi BM25 thuần túy

Hệ thống sử dụng công thức BM25 tính toán dựa trên các tham số:

* **`doc_lengths.pkl`**: Lưu độ dài (số từ) của 1.8 triệu văn bản để chuẩn hóa trọng số (b = 0.75).
* **TF Saturation**: k1 = 1.2 giúp kiểm soát mức độ ảnh hưởng của tần suất từ.
* **IDF (Inverse Document Frequency)**: Tính toán mức độ quan trọng của từ trên quy mô toàn corpus.

### 4.2. Cải tiến Coordination Boost

Khắc phục nhược điểm của toán tử OR mặc định trong BM25:

* **Công thức**: `FinalScore = BM25Score * (nMatched / nQuery)^2`
* **Ý nghĩa**: Ưu tiên cực mạnh cho các văn bản chứa đầy đủ các từ khóa trong truy vấn.

### 4.3. Metadata On-demand & Display

* **`doc_offsets.pkl`**: Lưu vị trí byte của từng dòng trong file nguồn. Khi cần hiển thị, hệ thống truy xuất trực tiếp từ file JSONL, giúp RAM tiêu thụ cực thấp.
* **Fallback Logic**: Tự động tìm kiếm ngành nghề từ nhiều trường dữ liệu (`industries_str_seg`, `str`, `detail`) để tránh trống thông tin Industry.

---

## 5. Tối ưu hóa Hiệu năng (Optimization)

| Kỹ thuật | Chi tiết | Kết quả |
| :--- | :--- | :--- |
| **Hot-loop Inlining** | Inline code tính điểm TF vào vòng lặp chính. | Giảm chi phí gọi hàm, search cực nhanh. |
| **Common Term Logic** | Tăng ngưỡng `max_df` lên 80% (giữ lại từ "xây dựng"). | Tăng Recall mà không làm chậm hệ thống. |
| **Smart Query Tokenizer** | Tích hợp `PyVi` tự động tách từ cho truy vấn. | Người dùng gõ tiếng Việt tự nhiên (không cần gạch dưới). |
| **Memory usage** | Chỉ load dictionary và offsets cần thiết. | **RAM < 60MB** cho 1.8M bản ghi. |

---

## 6. Thống kê Index (Index Statistics)

| Chỉ số | Giá trị |
| :--- | :--- |
| **Tổng số văn bản (N)** | 1.842.525 |
| **Số từ vựng duy nhất (Vocabulary)** | 695.470 |
| **Độ dài trung bình văn bản (Avgdl)** | 185.9 từ |
| **Kích thước Dictionary** | 18.3 MB |
| **Kích thước Postings (.bin)** | 1.04 GB |
| **Thời gian khởi động Searcher** | ~0.7 - 1.0 giây |

---

## 7. Hướng dẫn sử dụng Search Console

1. **Khởi chạy**: `python src/search_console.py`
2. **Lệnh đặc biệt**:
    * `:stats`: Xem thông tin chi tiết về Index.
    * `:top N`: Thay đổi số lượng kết quả hiển thị (mặc định 10).
    * `:help`: Xem hướng dẫn sử dụng.
3. **Ví dụ tìm kiếm**: `xây dựng Hà Nội`, `công nghệ thông tin`, `vận tải Hồ Chí Minh`.

---

## 8. Giải trình về Quy mô Từ vựng (Vocabulary Size)

Có sự chênh lệch lớn về số lượng Vocab giữa Milestone 1 (~18k) và Milestone 2 (~695k) do:

* **Phạm vi thống kê**: Ở M1, con số 18k chỉ ước tính dựa trên ngôn ngữ tự nhiên (Reviews).
* **Thực tế Indexing (M2)**: Hệ thống đánh chỉ mục cho toàn bộ trường dữ liệu của 1.8 triệu doanh nghiệp. Vocabulary hiện tại bao gồm mọi **Token duy nhất** (tên riêng, mã ngành, số nhà, ngách, ngõ, tên phố...) trên khắp Việt Nam. Đây là điều kiện bắt buộc để đảm bảo khả năng tìm kiếm chính xác (Precision) cho các thực thể doanh nghiệp.

---
*Báo cáo Milestone 2 - Nhóm OverFitting - SEG301.*
