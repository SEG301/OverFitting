# BÁO CÁO TỔNG KẾT MILESTONE 2: HỆ THỐNG TÌM KIẾM THÔNG TIN DOANH NGHIỆP THÔNG MINH

**Học phần**: Search Engines & Information Retrieval (SEG301)  
**Nhóm**: OverFitting  
**Thành viên**: Nguyễn Thanh Trà, Phan Đỗ Thanh Tuấn, Châu Thái Nhật Minh

---

## 1. Mục tiêu và Tầm nhìn Dự án

Trong giai đoạn Milestone 2, mục tiêu cao nhất của nhóm OverFitting là xây dựng một nền tảng tìm kiếm mạnh mẽ, có khả năng xử lý lượng dữ liệu lớn. Nhóm mong muốn tạo ra một công cụ mà người dùng có thể tìm thấy thông tin của bất kỳ doanh nghiệp nào tại Việt Nam chỉ trong 1s, với độ chính xác và tin cậy cao nhất.

Nguyên tắc xây dựng: Tự xây dựng mọi thành phần cốt lõi của bộ máy tìm kiếm để hiểu rõ bản chất vấn đề, thay vì phụ thuộc vào các thư viện có sẵn.

---

## 2. Quy mô Dữ liệu

Hệ thống được triển khai trên tập dữ liệu thực tế lớn:

- **Số lượng tài liệu**: 1.842.525 doanh nghiệp trên toàn quốc.
- **Kích thước dữ liệu thô**: Hơn 6.2 GB (định dạng JSONL).
- **Độ đa dạng**: Bao quát đầy đủ các thông tin từ tên công ty, mã số thuế, địa chỉ, người đại diện cho đến các ngành nghề kinh doanh.

---

## 3. Cấu trúc và Chức năng các thành phần

Hệ thống được tổ chức thành các khối chuyên biệt để xử lý dữ liệu quy mô lớn một cách ổn định:

- **`src/indexer/spimi.py`**: Trái tim của quá trình "Lưu kho", thực hiện đọc 1.8 triệu bản ghi và phân loại từ khóa vào bộ nhớ đệm.
- **`src/indexer/merging.py`**: Chịu trách nhiệm tổng hợp các phần dữ liệu đã phân loại thành một bộ từ điển hoàn chỉnh, giúp việc tìm kiếm không bị phân tán.
- **`src/ranking/bm25.py`**: Bộ não của hệ thống, chứa thuật toán tính toán và xếp hạng để đảm bảo các kết quả phù hợp nhất luôn nằm ở đầu danh sách.
- **`src/search_console.py`**: Giao diện điều khiển cho phép người dùng nhập từ khóa và hiển thị các thông tin tìm được một cách trực quan.

**Các tệp dữ liệu cốt lõi (trong `data/index`):**

- **`postings.bin`**: "Kho chứa" khổng lồ lưu danh sách các công ty chứa từng từ khóa. Đây là tệp nặng nhất (~1.1GB) nhưng đã được nén tối ưu.
- **`term_dict.pkl`**: "Cuốn từ điển" giúp máy tính tra cứu nhanh vị trí của từ khóa trong kho chứa, giúp việc tìm kiếm diễn ra tức thì.
- **`doc_lengths.pkl`**: Lưu trữ độ dài của từng doanh nghiệp để hỗ trợ việc chấm điểm công bằng giữa công ty có mô tả ngắn và dài.
- **`doc_offsets.pkl`**: "Bản đồ vị trí" giúp máy tính tìm thấy thông tin chi tiết (địa chỉ, ngành nghề) của doanh nghiệp từ file gốc 6GB mà không cần đọc lại từ đầu.

---

## 4. Cách thức Hệ thống Vận hành

Để hệ thống chạy nhanh và không làm treo máy, nhóm đã triển khai thông qua hai quy trình chính:

### 4.1. Quy trình "Lưu kho" dữ liệu (Indexing)

Hãy tưởng tượng việc tìm kiếm trong 1.8 triệu tờ giấy rời rạc. Nếu đọc từng tờ sẽ mất hàng tiếng đồng hồ. Nhóm đã thực hiện:

- **Xếp loại từ khóa**: Máy tính sẽ đọc qua toàn bộ doanh nghiệp, tách ra các từ quan trọng (ví dụ: "Xây dựng", "Hà Nội", "Công nghệ").
- **Ghi chép vị trí**: Với mỗi từ, máy sẽ lưu lại danh sách các công ty chứa từ đó.
- **Đóng gói thông minh**: Thay vì để dữ liệu rời rạc trên đĩa, nhóm đã nén và đóng gói lại chỉ còn **1.1GB** giúp việc truy xuất nhanh chóng hơn.

### 4.2. Quy trình "Tìm kiếm & Xếp hạng" (Ranking)

Khi người dùng nhập một câu hỏi, hệ thống thực hiện các bước sau:

1. **Hiểu ý định**: Tách câu hỏi của bạn thành các từ có nghĩa (ví dụ: tìm "Công ty du lịch" sẽ hiểu bạn đang tìm ngành nghề).
2. **Truy tìm nhanh**: Nhờ có "bản đồ vị trí" đã lập ở bước lưu kho, máy tính nhảy thẳng đến các kết quả liên quan mà không cần đọc lại toàn bộ dữ liệu.
3. **Chấm điểm ưu tiên**: Một kết quả được đưa lên đầu nếu thỏa mãn:
    - Tên công ty khớp hoàn toàn với từ khóa.
    - Xuất hiện nhiều lần trong nội dung.
    - Có chứa đồng thời tất cả các từ mà bạn đã nhập.
4. **Lấy thông tin tức thời**: Toàn bộ địa chỉ, mã số thuế chỉ được máy tính đọc ra khi bạn thực sự nhìn thấy trên màn hình, giúp tiết kiệm bộ nhớ tối đa.

---

## 5. Những kết quả đạt được

Nhóm đã đạt được những chỉ số vận hành lý tưởng, vượt xa kỳ vọng ban đầu:

- **Tốc độ phản hồi**: Trung bình chỉ mất <1s để trả về 10 kết quả tốt nhất.
- **Hiệu quả bộ nhớ**: Chỉ tốn khoảng <100MB RAM để chạy công cụ tìm kiếm.
- **Độ sạch dữ liệu**: Hệ thống tự động sửa các lỗi địa chỉ thường gặp, lọc bỏ các ký tự rác.
- **Tìm kiếm tiếng Việt chuẩn**: Xử lý tốt các từ ghép tiếng Việt (ví dụ: "bất động sản" được hiểu là một cụm từ duy nhất thay vì ba từ rời rạc).

---

## 6. Định hướng Phát triển (Milestone 3)

Trong chặng đường cuối cùng, nhóm hướng tới sự hoàn thiện cuối cùng:

- **Giao diện**: Xây dựng trang web tìm kiếm trực quan, mượt mà và dễ dùng.
- **Bộ lọc chuyên sâu**: Cho phép người dùng lọc công ty theo tỉnh thành, theo tình trạng hoạt động hoặc theo độ phủ của ngành nghề.

---
Nhóm OverFitting - Báo cáo Milestone 2 (Bản tổng hợp toàn diện & Chi tiết)
