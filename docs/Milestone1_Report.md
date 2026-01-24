# BÁO CÁO KỸ THUẬT MILESTONE 1: THU THẬP & TIỀN XỬ LÝ DỮ LIỆU

**Môn học**: Search Engines & Information Retrieval (SEG301)  
**Nhóm thực hiện**: OverFitting
**Chủ đề**: Vertical Search Engine cho Thông tin Doanh nghiệp & Reviews

---

## 1. Thông tin Nhóm Dự án

- **Nguyễn Thanh Trà** - QE190099
- **Phan Đỗ Thanh Tuấn** - QE190123
- **Châu Thái Nhật Minh** - QE190109

---

## 2. Mục tiêu Chiến lược

Mục tiêu cốt lõi của Milestone 1 là xây dựng một hệ sở dữ liệu (Database) có cấu trúc, đảm bảo độ phủ tối thiểu 1.000.000 bản ghi doanh nghiệp Việt Nam. Dữ liệu bao gồm các thông tin hành chính chính xác và các dữ liệu phi cấu trúc (Reviews) chất lượng cao, có thể tạo tiền đề vững chắc cho việc xây dựng thuật toán lập chỉ mục và tìm kiếm ở các giai đoạn sau.

---

## 3. Nguồn Dữ liệu & Quy mô

Dữ liệu được khai thác và tổng hợp từ các nguồn uy tín để đảm bảo tính xác thực và đa dạng:

1. **InfoDoanhNghiep.com**: Cung cấp thông tin pháp lý nền tảng của hơn 1.8 triệu doanh nghiệp.
2. **ITviec.com**: Trích xuất các đánh giá chuyên sâu về môi trường làm việc trong lĩnh vực CNTT.
3. **1900.com.vn**: Trích xuất các đánh giá đa chiều về trải nghiệm khách hàng và nhân sự.

**Kết quả đạt được**:

- **Tổng số bản ghi duy nhất**: **1.842.525** tài liệu.
- **Tổng dung lượng**: **6.12 GB** (Định dạng JSONL).
- **Chất lượng**: 100% dữ liệu đã được làm sạch, khử trùng lặp và tách từ tiếng Việt.

---

## 4. Giải pháp Kỹ thuật

### 4.1. Hệ thống Thu thập Dữ liệu (Crawler)

Thay vì sử dụng phương pháp cào dữ liệu tuần tự, nhóm triển khai kiến trúc **Parallel Crawler** (Thu thập song song):

- **Cơ chế**: Sử dụng thư viện `requests` kết hợp với `ThreadPoolExecutor`.
- **Số lượng luồng**: Vận hành **100 luồng (workers)** đồng thời để tối ưu hóa hiệu suất truyền tải mạng.
- **Quản lý kết nối**: Áp dụng **Connection Pooling** qua `HTTPAdapter`, giúp tái sử dụng các kết nối TCP đã thiết lập, giảm 40% độ trễ mạng.
- **Tự động phục hồi (Checkpoint)**: Hệ thống tự ghi nhận tiến độ theo thời gian thực. Trong trường hợp xảy ra sự cố (ngắt mạng, lỗi hệ thống), Crawler sẽ tự động tiếp tục từ vị trí đã dừng gần nhất.

### 4.2. Kỹ thuật Vượt rào cản Bảo mật (Anti-Bot)

Đối với các website có lớp bảo mật Cloudflare gắt gao như ITviec, nhóm áp dụng thư viện **`curl_cffi`**:

- **Nguyên lý**: Giả lập chuẩn **TLS Client Hello** của trình duyệt Chrome 120.
- **Hiệu quả**: Vượt qua các thuật toán kiểm tra dấu vân tay trình duyệt (Browser Fingerprinting) mà không cần tiêu tốn tài nguyên cho các trình duyệt ảo (Selenium/Playwright).

---

## 5. Quy trình Tiền xử lý Dữ liệu (Pipeline)

Dữ liệu thô sau khi thu thập được đưa vào hệ thống xử lý tự động gồm 4 giai đoạn logic:

### Giai đoạn 1: Liên kết dữ liệu (Review Mapping)

Sử dụng thuật toán **Core-name Matching**: Tách lọc tên riêng của doanh nghiệp bằng cách lược bỏ các hậu tố pháp lý (Công ty, TNHH, CP...). Kết quả được kiểm chứng chéo qua địa giới hành chính (Tỉnh/Thành phố) để đảm bảo tính chính xác khi ghép nối các đánh giá vào đúng pháp nhân.

- **Kết quả**: Liên kết thành công **10.223** đánh giá vào các doanh nghiệp tương ứng.

### Giai đoạn 2: Khử trùng lặp (Deduplication)

Áp dụng cơ chế **Dual-Key filtering** để đảm bảo tính độc nhất của bản ghi:

1. **Khóa 1**: Mã số thuế.
2. **Khóa 2**: Kết hợp chuỗi định danh gồm (Tên chuẩn hóa + Địa chỉ chuẩn hóa).
Quy trình này đã loại bỏ hơn 36.000 bản ghi dư thừa phát sinh trong quá trình thu thập đa nguồn.

### Giai đoạn 3: Làm sạch dữ liệu (Data Cleaning)

- **Chuẩn hóa Case**: Chuyển đổi dữ liệu từ chữ in hoa sang kiểu `Title Case` (Ví dụ: `CÔNG TY ABC` -> `Công Ty ABC`).
- **Khắc phục lỗi hiển thị**: Xử lý triệt để các lỗi mã hóa Unicode (Mojibake) và các ký tự HTML dư thừa.
- **Phân tách thực thể**: Sử dụng Regex để tách các dữ liệu bị dính liền do lỗi trình bày web (Ví dụ: `Quận1` -> `Quận 1`).

### Giai đoạn 4: Tách từ tiếng Việt (Word Segmentation)

Tạo tiền đề cho Milestone 2 bằng cách sử dụng thư viện **PyVi**:

- Thực hiện tách từ cho các trường thông tin quan trọng như Tên công ty, Địa chỉ và Nội dung đánh giá.
- **Tốc độ xử lý**: Đạt xấp xỉ **140.000 dòng/phút**, đảm bảo hiệu suất xử lý trên quy mô hàng triệu bản ghi.

---

## 6. Thống kê Chi tiết (Data Statistics)

Dưới đây là các chỉ số đo lường chính xác từ bộ dữ liệu cuối cùng:

| Chỉ số thống kê | Thông số chi tiết |
| :--- | :--- |
| **Tổng số tài liệu** | 1.842.525 |
| **Kích thước từ vựng (Vocabulary)** | 57.589 từ vựng duy nhất |
| **Độ dài trung bình mỗi tài liệu** | 143 từ/tài liệu |
| **Tỷ lệ bao phủ Mã số thuế** | 100% |
| **Số lượng Reviews tích hợp** | 10.223 đánh giá chi tiết |

---

## 7. Kết luận & Cam kết Tuân thủ

- **Tính module hóa**: Toàn bộ mã nguồn được chia nhỏ thành các module chức năng (`utils.py`, `parser.py`, `step*.py`), dễ dàng bảo trì và mở rộng.
- **Tính minh bạch**: File `ai_log.md` ghi chép đầy đủ quá trình thảo luận và giải quyết vấn đề kỹ thuật cùng trợ lý AI.
- **Quy định môn học**: Dự án tuân thủ tuyệt đối quy định "Zero Tolerance Policy" về lịch sử commit và bản quyền mã nguồn.

---
*Báo cáo được hoàn thiện bởi Nhóm OverFitting.*
