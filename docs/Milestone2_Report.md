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

### 3.1. Thuật toán SPIMI

Nhóm triển khai thuật toán SPIMI để giải quyết bài toán tràn bộ nhớ khi xử lý 1.8 triệu bản ghi:

* **Block-based processing**: Dữ liệu được chia thành từng khối (50,000 docs/block). Mỗi khối được đánh chỉ mục trong RAM và ghi xuống đĩa dưới dạng file Pickle tạm thời.
* **K-way Merge**: Sử dụng cấu trúc `heapq` (Min-heap) để gộp các block file đã sắp xếp theo thứ tự alphabet thành một Inverted Index hoàn chỉnh duy nhất.

### 3.2. Cấu trúc Index 2-File (Memory-Efficient Architecture)

Để đạt tốc độ search nhanh mà không tốn RAM, nhóm thiết kế hệ thống lưu trữ tách biệt:

1. **`term_dict.pkl` (~18 MB)**: Lưu mapping từ khóa sang vị trí byte (offset) và độ dài trong file postings. Chỉ file này được load vào RAM khi khởi động.
2. **`postings.bin` (~1.04 GB)**: Lưu danh sách postings (doc_id, term_freq) dưới dạng nhị phân. Dữ liệu được đọc trực tiếp từ đĩa thông qua `f.seek()`, giúp RAM tiêu thụ cực thấp (~55 MB).

---

## 4. Thuật toán Xếp hạng (Ranking)

### 4.1. Cốt lõi BM25

Hệ thống sử dụng công thức BM25 thuần túy (Code tay 100%, không dùng thư viện IR):

* **TF Saturation**: Điều chỉnh sự bão hòa của tần suất từ (k1 = 1.2).
* **Length Normalization**: Điều chỉnh trọng số theo độ dài văn bản (b = 0.75).
* **IDF (Inverse Document Frequency)**: Tính toán mức độ quan trọng của từ dựa trên quy mô toàn bộ 1.8 triệu docs.

### 4.2. Cải tiến Coordination Boost

Để khắc phục nhược điểm của toán tử OR trong BM25, nhóm triển khai hệ số phối hợp:

* **Công thức**: `FinalScore = BM25Score * (nMatched / nQuery)^2`
* **Ý nghĩa**: Ưu tiên cực mạnh cho các văn bản chứa đầy đủ các từ khóa trong truy vấn (ví dụ: tìm "xây dựng Hà Nội" sẽ loại bỏ các doanh nghiệp chỉ chứa "Hà Nội" nhưng thuộc ngành khác).

### 4.3. Metadata Fallback & Display

* **Metadata On-demand**: Lưu `doc_offsets.pkl` để tìm thông tin công ty trực tiếp từ file JSONL gốc khi hiển thị, không lưu metadata vào Index.
* **Fallback Logic**: Tự động tìm kiếm ngành nghề từ nhiều trường dữ liệu khác nhau (`industries_str_seg`, `str`, `detail`) để đảm bảo không bị trống thông tin Industry.

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

## 8. Cấu trúc Thư mục & Giải thích Tệp tin

### 8.1. Thư mục `src/` (Mã nguồn hệ thống)

* **`search_console.py`**: Điểm điều khiển chính của ứng dụng. Cung cấp giao diện dòng lệnh (CLI) để người dùng nhập truy vấn và xem kết quả trực quan.
* **`indexer/spimi.py`**: Thực hiện giai đoạn Indexing đầu tiên. Đọc dữ liệu JSON thô, tách từ, và tạo ra các chỉ mục con (blocks) để tránh quá tải RAM.
* **`indexer/merging.py`**: Thực hiện quá trình K-way merge, trộn các chỉ mục con thành bộ chỉ mục cuối cùng theo cấu trúc 2-file tối ưu.
* **`ranking/bm25.py`**: Chứa logic chính của thuật toán BM25, Coordination Boost và cơ chế đọc Metadata on-demand để tối ưu RAM.

### 8.2. Thư mục `data/index/` (Dữ liệu chỉ mục)

* **`term_dict.pkl`**: Từ điển từ vựng (Vocabulary). Lưu mapping giữa từ khóa và vị trí lưu trữ của nó trong file danh sách postings.
* **`postings.bin`**: File chứa danh sách các văn bản (postings lists) dưới dạng nhị phân, được thiết kế để truy xuất ngẫu nhiên cực nhanh.
* **`doc_lengths.pkl`**: Danh sách độ dài của 1.8 triệu văn bản, phục vụ cho việc tính toán trọng số chuẩn hóa trong BM25.
* **`doc_offsets.pkl`**: Bản đồ vị trí byte của từng công ty trong file dữ liệu gốc, giúp hiển thị thông tin ngay lập tức mà không cần load metadata vào RAM.

---
*Báo cáo Milestone 2 - Nhóm OverFitting - SEG301.*
