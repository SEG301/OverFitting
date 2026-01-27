# BÁO CÁO KỸ THUẬT MILESTONE 1: THU THẬP & TIỀN XỬ LÝ DỮ LIỆU

**Môn học**: Search Engines & Information Retrieval (SEG301)  
**Nhóm thực hiện**: OverFitting  
**Chủ đề**: Vertical Search Engine cho Thông tin Doanh nghiệp & Reviews

---

## 1. Thông tin thành viên

* **Nguyễn Thanh Trà** - QE190099
* **Phan Đỗ Thanh Tuấn** - QE190123
* **Châu Thái Nhật Minh** - QE190109

---

## 2. Mục tiêu

Mục tiêu cốt lõi của Milestone 1 là chuyển đổi dữ liệu thô từ môi trường web thành một **bộ dữ liệu có cấu trúc (Structured Dataset)**. Bộ dữ liệu này đảm bảo:

* **Quy mô**: Đạt mốc **1.842.525** bản ghi (vượt xa mục tiêu 1.000.000 ban đầu).
* **Sẵn sàng cho Indexing**: Dữ liệu đã được làm sạch và tách từ (Segmentation), sẵn sàng làm đầu vào cho các thuật toán đánh chỉ mục ở Milestone 2.

---

## 3. Nguồn Dữ liệu & Quy mô

Dữ liệu được khai thác từ 3 nguồn bổ trợ lẫn nhau:

1. **InfoDoanhNghiep.com**: Cung cấp thông tin pháp lý (Tên công ty, Mã số thuế, Địa chỉ, Ngày thành lập, Người đại diện...) của hơn 1.8 triệu doanh nghiệp Việt Nam.
2. **ITviec.com**: Trích xuất các đánh giá chuyên sâu về môi trường làm việc, chế độ đãi ngộ đặc thù trong lĩnh vực Công nghệ thông tin.
3. **1900.com.vn**: Một nguồn dữ liệu cung cấp đánh giá về môi trường làm việc cho nhân sự.

**Kết quả đạt được**:

* **Tổng số bản ghi**: 1.842.525 tài liệu.
* **Dung lượng**: 6.2 GB (Định dạng JSONL).
* **Định dạng lưu trữ**: Mọi bản ghi được lưu trữ dưới dạng JSON Lines, mỗi dòng là một đối tượng có schema thống nhất.

---

## 4. Giải pháp Kỹ thuật

### 4.1. Cấu trúc Thư mục Source Code

Để đảm bảo tính module hóa và dễ bảo trì, mã nguồn được tổ chức như sau:

```text
src/crawler/
├── crawl_enterprise.py      # Thu thập thông tin doanh nghiệp (Parallel)
├── crawl_reviews.py         # Thu thập đánh giá (ITviec, 1900)
├── step1_mapping.py         # Liên kết reviews vào doanh nghiệp
├── step2_deduplicate.py     # Lọc trùng lặp
├── step3_cleaning.py        # Làm sạch HTML, font, Unicode
├── step4_segmentation.py    # Tách từ tiếng Việt (NLP)
├── run_pipeline.py          # Quản lý luồng xử lý tự động
├── parser.py                # Logic bóc tách HTML chuyên biệt
└── utils.py                 # Hàm tiện ích chuẩn hóa
```

### 4.2. Hệ thống Thu thập Dữ liệu (Crawler)

Nhóm triển khai kiến trúc **Parallel Crawler** thay vì thu thập tuần tự:

* **Tối ưu luồng**: Vận hành **50 threads** đồng thời với `ThreadPoolExecutor`, giúp rút ngắn thời gian thu thập so với phương pháp thông thường.
* **Quản lý kết nối**: Duy trì các kết nối mạng sẵn có (Connection Pooling) để dùng lại cho các yêu cầu sau, giúp tiết kiệm thời gian khởi tạo lại từ đầu cho mỗi bản ghi.
* **Cơ chế Checkpoint (Smart Resume)**: Tự động phân tích tệp đầu ra để xác định tiến độ của từng khu vực, từ đó tính toán chính xác số trang cần cào tiếp theo mà không cần tệp trung gian.

### 4.3. Kỹ thuật Vượt rào cản (Anti-Bot)

Thay vì sử dụng các trình duyệt ảo (Selenium/Playwright) tốn tài nguyên, nhóm áp dụng **`curl_cffi`**:

* **Giả lập TLS Fingerprint**: Bắt chước chuẩn *TLS Client Hello* của Chrome 120. điều này cho phép vượt qua các lớp bảo vệ của Cloudflare mà không bị nhận diện là bot.
* **Hiệu quả**: Tiết kiệm RAM và CPU hơn so với trình duyệt không đầu (Headless Browser).

---

## 5. Quy trình Xử lý Dữ liệu (Data Pipeline)

Quy trình biến dữ liệu "thô" thành dữ liệu "sạch" qua 4 giai đoạn:

### Giai đoạn 1: Liên kết dữ liệu (Review Mapping)

Sử dụng phương pháp **Core-name Matching**:

* Loại bỏ các thuật ngữ pháp lý dư thừa (như "Công ty", "TNHH", "CP"...) và chuẩn hóa văn bản để trích xuất tên định danh thực tế (ví dụ: giúp khớp nối "Công ty TNHH FPT" và "FPT" thành cùng một đối tượng).
* Khớp nối hàng chục nghìn reviews từ các trang đánh giá vào đúng doanh nghiệp dựa trên tên định danh đã chuẩn hóa.

### Giai đoạn 2: Khử trùng lặp (Deduplication)

Áp dụng cơ chế **Triple-Key filtering** để đảm bảo tính duy nhất:

* **Khóa định danh**: Kết hợp bộ ba (Mã số thuế + Tên chuẩn hóa + Địa chỉ chuẩn hóa).
* **Tác dụng**: Loại bỏ các bản ghi trùng lặp phát sinh khi thu thập dữ liệu từ nhiều nguồn hoặc cào lại nhiều lần, đảm bảo mỗi doanh nghiệp chỉ xuất hiện một lần duy nhất.

### Giai đoạn 3: Làm sạch dữ liệu (Data Cleaning)

* Xử lý **Unicode/Mojibake**: Khắc phục các lỗi hiển thị tiếng Việt do sai lệch mã hóa web.
* **Regex Processing**: Sửa lỗi trình bày như dính chữ (ví dụ: `HàNội` -> `Hà Nội`) và loại bỏ các thẻ HTML rác còn sót lại.

### Giai đoạn 4: Tách từ tiếng Việt (Word Segmentation)

Sử dụng thư viện **PyVi**:

* Đây là bước then chốt cho Milestone 2. Việc tách từ giúp Search Engine hiểu được các từ ghép tiếng Việt (ví dụ: `môi_trường`, `phát_triển`), nâng cao độ chính xác của thuật toán tìm kiếm.
* Toàn bộ hơn 1.8 triệu bản ghi đã được tách từ tự động.

---

## 6. Thống kê Chi tiết (Data Statistics)

| Chỉ số thống kê | Thông số chi tiết |
| :--- | :--- |
| **Tổng số tài liệu** | 1.842.525 |
| **Số lượng từ vựng (Vocabulary)** | 18.087 từ vựng duy nhất |
| **Độ dài trung bình mỗi tài liệu** | 143 từ/tài liệu |
| **Số lượng Reviews tích hợp** | 10.223 đánh giá chi tiết |
| **Dung lượng file tổng** | 6.2 GB |

---

## 7. Kết luận & Cam kết

Bộ dữ liệu Milestone 1 hiện đã đạt trạng thái: Sạch, có cấu trúc, quy mô lớn và đã được xử lý. Đây có thể là nền tảng vững chắc để nhóm triển khai hệ thống Indexing và Ranking ở Milestone tiếp theo.

---
*Báo cáo được hoàn thiện bởi Nhóm OverFitting - SEG301.*
