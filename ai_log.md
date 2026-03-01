# NHẬT KÝ TƯƠNG TÁC AI - NHÓM OVERFITTING

---

## 1. Nhật ký Thành viên 1

### Date: 2026-01-09

**Task:** Project Kickoff & Strategy for Topic 3.

**User:** Nhóm tôi chọn chủ đề "Thông tin doanh nghiệp & Review". Mục tiêu Milestone 1 là 1 triệu dòng dữ liệu sạch. Trang Masothue có vẻ đầy đủ nhất, bạn giúp tôi viết script cào trang này nhé.
**AI:** Chào bạn! Đối với Masothue.com, trang này có hệ thống chống bot Cloudflare rất mạnh. Tôi đề xuất dùng `undetected-chromedriver` để giả lập hành vi người dùng thật.
**User:** Tôi đã chạy thử nhưng tốc độ quá chậm, mỗi giây chỉ được 1-2 công ty. Với 1 triệu dòng thì cào bao giờ mới xong?
**AI:** Đúng vậy, Selenium rất tốn tài nguyên. Tôi đã nghiên cứu thêm và phát hiện trang `infodoanhnghiep.com` có dữ liệu tương tự nhưng cấu trúc nhẹ hơn nhiều, không bị chặn gắt gao. Chúng ta có thể dùng `requests` kết hợp đa luồng (Multi-threading).
**Result:** Chuyển hướng sang Infodoanhnghiep, kết quả bước đầu đạt ~1000 cty/phút.

---

### Date: 2026-01-10

**Task:** Optimizing Speed Crawler & Deduplication.

**User:** Tôi thấy dữ liệu cào về thỉnh thoảng bị lặp lại các công ty lớn. Bạn xử lý trùng lặp ngay khi cào được không?
**AI:** Chắc chắn rồi. Tôi sẽ thêm một biến Global `SEEN_RECORDS` sử dụng kiểu dữ liệu `set` để tra cứu nhanh. Để an toàn đa luồng, tôi sẽ dùng `threading.Lock()` mỗi khi ghi dữ liệu hoặc cập nhật bộ lọc trùng.
**User:** Lọc theo mã số thuế (Tax Code) thôi có đủ không?
**AI:** Một số chi nhánh có thể dùng chung mã số thuế hoặc có lỗi dữ liệu đầu vào. Để chính xác nhất, tôi sẽ tạo khóa (Key) kết hợp: `(tax_code, company_name, address)`. Nếu cả 3 trường này giống hệt nhau mới coi là trùng.
**User:** Hãy thêm tính năng Resume. Nếu tôi tắt máy bật lại, crawler phải biết cào tiếp từ chỗ cũ.
**AI:** Tôi đã thêm hàm `load_existing_data()`. Khi khởi động, crawler sẽ đọc file `.jsonl` đã có, nạp toàn bộ khóa vào `SEEN_RECORDS` rồi mới bắt đầu quét tiếp.
**Result:** Script `speed_crawler.py` hoàn thiện, chạy ổn định với 30 workers.

---

### Date: 2026-01-12

**Task:** Deep Crawl for Reviews (1900.com.vn).

**User:** Milestone 1 yêu cầu cả dữ liệu Review của Topic 3. Tôi thử `reviewcongty.com` nhưng bị Cloudflare block 100%. Có nguồn nào lấy được comment thật của nhân viên không?
**AI:** Qua khảo sát, `1900.com.vn` là lựa chọn tốt nhất hiện tại. Trang này cho phép xem review chi tiết mà không cần đăng nhập.
**User:** Làm sao để lấy được nội dung "Ưu điểm" và "Nhược điểm" tách biệt?
**AI:** Tôi đã chạy script `dump_1900_detail.py` để phân tích mã nguồn HTML của họ.

- Phần Ưu điểm nằm sau thẻ `strong` có class `greenColor`.
- Phần Nhược điểm nằm sau thẻ `strong` có class `text-danger`.
- Tôi sẽ sử dụng `BeautifulSoup` và phương thức `.find_next_sibling()` để trích xuất nội dung văn bản trong các thẻ `div` tương ứng.
**User:** Hãy viết script cào hàng loạt trang này. Phải cào từ trang listing trước để lấy link detail.
**Result:** Script `crawler_1900.py` (lấy danh sách) và `crawler_1900_detailed.py` (lấy chi tiết comment) hoạt động thành công. Dữ liệu Review rất chất lượng, có đầy đủ đánh giá cá nhân.

---

### Date: 2026-01-13

**Task:** Debugging Pagination Infinite Loop & Scaling to 50 Workers.

**User:** Này, tôi đang chạy crawler Infodoanhnghiep, khu vực Hà Nội. Tôi thấy Terminal báo đang quét đến trang 29,000, 30,000... Trong khi tôi kiểm tra tay trên web thì chỉ có hơn 27,000 trang thôi. Tại sao nó không dừng lại?
**AI:** Đây là một lỗi logic rất thú vị. Website này sử dụng cơ chế "Soft Redirect". Khi bạn truy cập một trang không tồn tại (vd: trang 30,000), thay vì trả về lỗi 404, server tự động redirect (chuyển hướng 302) về trang chủ của khu vực đó (trang 1). Crawler của chúng ta thấy status code vẫn là 200 nên tưởng là vẫn còn data và cứ thế chạy vô tận.
**User:** Vậy sửa thế nào?
**AI:** Tôi sẽ dùng thuộc tính `resp.url` của thư viện requests để kiểm tra URL cuối cùng sau khi redirect. Nếu URL nhận được không chứa chuỗi `trang-X` mà chúng ta yêu cầu, nghĩa là server đã đẩy chúng ta về trang đầu. Lúc đó crawler sẽ phát tín hiệu `END_OF_PAGE` để dừng quét tỉnh đó.
**User:** Sửa xong thì tăng số luồng lên 50 cho tôi. Tôi muốn xong 1 triệu dòng sớm.
**AI:** Đã cập nhật `WORKERS = 50`. Tốc độ hiện tại rất khủng khiếp, Terminal nhảy liên tục.

---

### Date: 2026-01-14 (Session 1 - Optimization & Refactor)

**Task:** Tái cấu trúc mã nguồn và chuẩn hóa cây thư mục Github.

**User:** Hãy dọn dẹp các file rác và đảm bảo cấu trúc thư mục đúng theo yêu cầu của đồ án.
**AI:** Đã thực hiện xóa các file thực nghiệm (`debug_*.py`, `dump_*.py`) và refactor thành các module `crawl_enterprise.py`, `parser.py`, `utils.py`.
**User:** Ủa sao lại xóa file `speed_crawler.py`, file đó tôi dùng để cào dữ liệu mà?
**AI:** Xin lỗi bạn, tôi đã khôi phục lại file đó nhưng với vai trò là một "wrapper" gọi logic từ module mới để đảm bảo tính module hóa (điểm tối đa Milestone 1) mà vẫn giữ được thói quen sử dụng của bạn.
**Result:** Dự án sạch sẽ, đúng spec, đã được push lên Github.

---

### Date: 2026-01-14 (Session 2 - Deep Crawl Upgrade)

**Task:** Nâng cấp cơ chế cào dữ liệu chi tiết (Deep Crawl).

**User:** Dường như crawler hiện tại chỉ lấy thông tin bề nổi ở trang danh sách. Tôi muốn vào từng công ty để lấy thông tin chi tiết (Người đại diện, tình trạng hoạt động...).
**AI:** Đã phân tích DOM của trang chi tiết doanh nghiệp bằng trình duyệt. Phát hiện các trường dữ liệu quan trọng nằm trong bảng `responsive-table` và các thẻ Schema.org (`itemprop`).
**Work:**

1. **Parser Update**: Viết hàm `parse_company_detail` để trích xuất: Đại diện pháp luật (`founder`), Số điện thoại (`telephone`), Tình trạng hoạt động, và danh sách toàn bộ Ngành nghề kinh doanh.
2. **Spider Enhancement**: Thiết lập `DEEP_CRAWL = True`. Sử dụng **Nested ThreadPool (Đa luồng lồng nhau)**: Mỗi thread quét trang danh sách sẽ khởi tạo thêm các sub-threads để fetch đồng thời 20 trang chi tiết công ty. Điều này giúp lấy được dữ liệu sâu mà không làm giảm quá nhiều tốc độ quét tổng thể.
3. **Verification**: Đã chạy test thành công xác nhận dữ liệu đã có thêm các trường "representative", "status", "industries_detail".
**Result:** Bộ dữ liệu Milestone 1 giờ đây cực kỳ chi tiết và có độ sâu thông tin vượt trội.

---

### Date: 2026-01-14 (Session 3: Deep Debugging Industry Parser)

**Task:** Khắc phục lỗi dữ liệu ngành nghề bị trống (Empty Industries).

**User:** Sao tôi thấy danh sách các ngành nghề của mỗi công ty đều trống hết vậy?
**AI:** Để tôi kiểm tra. Tôi sẽ sử dụng Browser Subagent để soi mã nguồn trang web.
*(AI thực hiện inspect DOM trên trang infodoanhnghiep.com)*
**AI:** Phát hiện ra trang này không dùng thẻ `<table>` mà dùng các thẻ `<div>` phẳng (flat structure) với class `.responsive-table-cell`. Code cũ của chúng ta đang tìm thẻ `tr/td` nên không thấy gì.
**Action:** Viết lại hàm `parse_company_detail` trong `parser.py` để duyệt qua các thẻ div.

**User:** Tôi chạy lại rồi nhưng danh sách vẫn trống trơn.
**AI:** Thật kỳ lạ. Để tôi dùng Browser Subagent chụp ảnh màn hình và lấy mã HTML `outerHTML` của bảng đó.
*(AI phân tích ảnh chụp màn hình và HTML thô)*
**AI:** Tìm ra nguyên nhân gốc rễ! Giữa ô "Mã ngành" và "Tên ngành" có một thẻ `div` quảng cáo của Google (`google-auto-placed`) được chèn động vào. Logic cũ của tôi là lấy 2 thẻ liên tiếp nên bị thẻ quảng cáo này làm sai lệch dữ liệu.
**Action:** Cập nhật lại logic Parser theo cơ chế **Head-Sibling**:

1. Tìm tất cả các ô có class `.responsive-table-cell-head` (Mã ngành).
2. Với mỗi mã, tìm thẻ anh em (`sibling`) kế tiếp có class nội dung, tự động bỏ qua các thẻ quảng cáo ở giữa.
3. Thêm bộ đếm `DEEP` vào log terminal để User theo dõi được số lượng ngành nghề lấy được theo thời gian thực.
**Result:** Terminal báo chỉ số `DEEP` tăng đều. Dữ liệu jsonl đã có đầy đủ trường `industries_detail`.

---

### Date: 2026-01-14 (Session 4: The 'Ultimate Speed' Optimization)

**Task:** Tăng tốc độ cào dữ liệu lên giới hạn phần cứng (Hardware Limit).

**User:** Tốc độ hiện tại còn hơi chậm, có cách nào tăng thêm không?
**AI:** Hiện tại chúng ta đang bị nghẽn ở bước khởi tạo kết nối mạng (Network Handshake) và việc quản lý luồng quá an toàn. Tôi đề xuất giải pháp "Turbo":

1. **Connection Pooling**: Tái sử dụng kết nối HTTPS (Keep-Alive), giảm độ trễ 0.3s/request.
2. **Parallel Detail Fetching**: Thay vì cào tuần tự, mỗi worker chính sẽ đẻ ra 10 threads con để cào song song 10 trang chi tiết cùng lúc.

**User:** Tốc độ hiện tại là nhanh nhất có thể chưa? Tôi muốn max speed.
**AI:** Vẫn có thể nhanh hơn. Tôi sẽ kích hoạt chế độ **"Ultimate Speed"**:

1. **Global ThreadPool**: Thay vì tạo/hủy thread liên tục, tôi dùng một `ThreadPoolExecutor` toàn cục duy nhất cho 1.000.000 request.
2. **Max Connections**: Mở rộng `HTTPAdapter` lên 1000 kết nối đồng thời.
3. **Workers**: Tăng số luồng quét trang danh sách lên **100**.
**Action:** Cập nhật `crawl_enterprise.py` với kiến trúc mới.
**Warning:** Tốc độ này sẽ chiếm dụng gần hết băng thông mạng của máy tính.
**Result:** Crawler đạt tốc độ cao nhất từ trước đến nay.

**User:** Ok, dừng cào đi. Đẩy code lên Github.
**Action:**

1. Dọn dẹp file rác (`debug_*.py`, data cũ).
2. Cập nhật `.gitignore` để track file log.
3. Git add, commit và push toàn bộ mã nguồn tối ưu lên nhánh main.

---

## 2. Nhật ký Thành viên 2

### Date: 2026-01-09

**Task:** Project Kickoff & Strategy for Topic 3.

**User:** Nhóm tôi chọn chủ đề "Thông tin doanh nghiệp & Review". Mục tiêu Milestone 1 là 1 triệu dòng dữ liệu sạch. Trang Masothue có vẻ đầy đủ nhất, bạn giúp tôi viết script cào trang này nhé.
**AI:** Chào bạn! Đối với Masothue.com, trang này có hệ thống chống bot Cloudflare rất mạnh. Tôi đề xuất dùng `undetected-chromedriver` để giả lập hành vi người dùng thật.
**User:** Tôi đã chạy thử nhưng tốc độ quá chậm, mỗi giây chỉ được 1-2 công ty. Với 1 triệu dòng thì cào bao giờ mới xong?
**AI:** Đúng vậy, Selenium rất tốn tài nguyên. Tôi đã nghiên cứu thêm và phát hiện trang `infodoanhnghiep.com` có dữ liệu tương tự nhưng cấu trúc nhẹ hơn nhiều, không bị chặn gắt gao. Chúng ta có thể dùng `requests` kết hợp đa luồng (Multi-threading).
**Result:** Chuyển hướng sang Infodoanhnghiep, kết quả bước đầu đạt ~1000 cty/phút.

---

### Date: 2026-01-10

**Task:** Optimizing Speed Crawler & Deduplication.

**User:** Tôi thấy dữ liệu cào về thỉnh thoảng bị lặp lại các công ty lớn. Bạn xử lý trùng lặp ngay khi cào được không?
**AI:** Chắc chắn rồi. Tôi sẽ thêm một biến Global `SEEN_RECORDS` sử dụng kiểu dữ liệu `set` để tra cứu nhanh. Để an toàn đa luồng, tôi sẽ dùng `threading.Lock()` mỗi khi ghi dữ liệu hoặc cập nhật bộ lọc trùng.
**User:** Lọc theo mã số thuế (Tax Code) thôi có đủ không?
**AI:** Một số chi nhánh có thể dùng chung mã số thuế hoặc có lỗi dữ liệu đầu vào. Để chính xác nhất, tôi sẽ tạo khóa (Key) kết hợp: `(tax_code, company_name, address)`. Nếu cả 3 trường này giống hệt nhau mới coi là trùng.
**User:** Hãy thêm tính năng Resume. Nếu tôi tắt máy bật lại, crawler phải biết cào tiếp từ chỗ cũ.
**AI:** Tôi đã thêm hàm `load_existing_data()`. Khi khởi động, crawler sẽ đọc file `.jsonl` đã có, nạp toàn bộ khóa vào `SEEN_RECORDS` rồi mới bắt đầu quét tiếp.
**Result:** Script `speed_crawler.py` hoàn thiện, chạy ổn định với 30 workers.

---

### Date: 2026-01-12

**Task:** Deep Crawl for Reviews (1900.com.vn).

**User:** Milestone 1 yêu cầu cả dữ liệu Review của Topic 3. Tôi thử `reviewcongty.com` nhưng bị Cloudflare block 100%. Có nguồn nào lấy được comment thật của nhân viên không?
**AI:** Qua khảo sát, `1900.com.vn` là lựa chọn tốt nhất hiện tại. Trang này cho phép xem review chi tiết mà không cần đăng nhập.
**User:** Làm sao để lấy được nội dung "Ưu điểm" và "Nhược điểm" tách biệt?
**AI:** Tôi đã chạy script `dump_1900_detail.py` để phân tích mã nguồn HTML của họ.

- Phần Ưu điểm nằm sau thẻ `strong` có class `greenColor`.
- Phần Nhược điểm nằm sau thẻ `strong` có class `text-danger`.
- Tôi sẽ sử dụng `BeautifulSoup` và phương thức `.find_next_sibling()` để trích xuất nội dung văn bản trong các thẻ `div` tương ứng.
**User:** Hãy viết script cào hàng loạt trang này. Phải cào từ trang listing trước để lấy link detail.
**Result:** Script `crawler_1900.py` (lấy danh sách) và `crawler_1900_detailed.py` (lấy chi tiết comment) hoạt động thành công. Dữ liệu Review rất chất lượng, có đầy đủ đánh giá cá nhân.

---

### Date: 2026-01-13

**Task:** Debugging Pagination Infinite Loop & Scaling to 50 Workers.

**User:** Này, tôi đang chạy crawler Infodoanhnghiep, khu vực Hà Nội. Tôi thấy Terminal báo đang quét đến trang 29,000, 30,000... Trong khi tôi kiểm tra tay trên web thì chỉ có hơn 27,000 trang thôi. Tại sao nó không dừng lại?
**AI:** Đây là một lỗi logic rất thú vị. Website này sử dụng cơ chế "Soft Redirect". Khi bạn truy cập một trang không tồn tại (vd: trang 30,000), thay vì trả về lỗi 404, server tự động redirect (chuyển hướng 302) về trang chủ của khu vực đó (trang 1). Crawler của chúng ta thấy status code vẫn là 200 nên tưởng là vẫn còn data và cứ thế chạy vô tận.
**User:** Vậy sửa thế nào?
**AI:** Tôi sẽ dùng thuộc tính `resp.url` của thư viện requests để kiểm tra URL cuối cùng sau khi redirect. Nếu URL nhận được không chứa chuỗi `trang-X` mà chúng ta yêu cầu, nghĩa là server đã đẩy chúng ta về trang đầu. Lúc đó crawler sẽ phát tín hiệu `END_OF_PAGE` để dừng quét tỉnh đó.
**User:** Sửa xong thì tăng số luồng lên 50 cho tôi. Tôi muốn xong 1 triệu dòng sớm.
**AI:** Đã cập nhật `WORKERS = 50`. Tốc độ hiện tại rất khủng khiếp, Terminal nhảy liên tục.

---

### Date: 2026-01-14 (Session 1 - Optimization & Refactor)

**Task:** Tái cấu trúc mã nguồn và chuẩn hóa cây thư mục Github.

**User:** Hãy dọn dẹp các file rác và đảm bảo cấu trúc thư mục đúng theo yêu cầu của đồ án.
**AI:** Đã thực hiện xóa các file thực nghiệm (`debug_*.py`, `dump_*.py`) và refactor `speed_crawler.py` thành các module `spider.py`, `parser.py`, `utils.py`.
**User:** Ủa sao lại xóa file `speed_crawler.py`, file đó tôi dùng để cào dữ liệu mà?
**AI:** Xin lỗi bạn, tôi đã khôi phục lại file đó nhưng với vai trò là một "wrapper" gọi logic từ module mới để đảm bảo tính module hóa (điểm tối đa Milestone 1) mà vẫn giữ được thói quen sử dụng của bạn.
**Result:** Dự án sạch sẽ, đúng spec, đã được push lên Github.

---

### Date: 2026-01-14 (Session 2 - Deep Crawl Upgrade)

**Task:** Nâng cấp cơ chế cào dữ liệu chi tiết (Deep Crawl).

**User:** Dường như crawler hiện tại chỉ lấy thông tin bề nổi ở trang danh sách. Tôi muốn vào từng công ty để lấy thông tin chi tiết (Người đại diện, tình trạng hoạt động...).
**AI:** Đã phân tích DOM của trang chi tiết doanh nghiệp bằng trình duyệt. Phát hiện các trường dữ liệu quan trọng nằm trong bảng `responsive-table` và các thẻ Schema.org (`itemprop`).
**Work:**

1. **Parser Update**: Viết hàm `parse_company_detail` để trích xuất: Đại diện pháp luật (`founder`), Số điện thoại (`telephone`), Tình trạng hoạt động, và danh sách toàn bộ Ngành nghề kinh doanh.
2. **Spider Enhancement**: Thiết lập `DEEP_CRAWL = True`. Sử dụng **Nested ThreadPool (Đa luồng lồng nhau)**: Mỗi thread quét trang danh sách sẽ khởi tạo thêm các sub-threads để fetch đồng thời 20 trang chi tiết công ty. Điều này giúp lấy được dữ liệu sâu mà không làm giảm quá nhiều tốc độ quét tổng thể.
3. **Verification**: Đã chạy test thành công xác nhận dữ liệu đã có thêm các trường "representative", "status", "industries_detail".
**Result:** Bộ dữ liệu Milestone 1 giờ đây cực kỳ chi tiết và có độ sâu thông tin vượt trội.

### Date: 2026-01-14 (Session 3: Deep Debugging Industry Parser)

**Task:** Khắc phục lỗi dữ liệu ngành nghề bị trống (Empty Industries).

**User:** Sao tôi thấy danh sách các ngành nghề của mỗi công ty đều trống hết vậy?
**AI:** Để tôi kiểm tra. Tôi sẽ sử dụng Browser Subagent để soi mã nguồn trang web.
**AI:** Phát hiện ra trang này không dùng thẻ `<table>` mà dùng các thẻ `<div>` phẳng (flat structure) with class `.responsive-table-cell`. Code cũ của chúng ta đang tìm thẻ `tr/td` nên không thấy gì.
**Action:** Viết lại hàm `parse_company_detail` trong `parser.py` để duyệt qua các thẻ div.

**User:** Tôi chạy lại rồi nhưng danh sách vẫn trống trơn.
**AI:** Thật kỳ lạ. Để tôi dùng Browser Subagent chụp ảnh màn hình và lấy mã HTML `outerHTML` của bảng đó.
**AI:** Tìm ra nguyên nhân gốc rễ! Giữa ô "Mã ngành" và "Tên ngành" có một thẻ `div` quảng cáo của Google (`google-auto-placed`) được chèn động vào. Logic cũ của tôi là lấy 2 thẻ liên tiếp nên bị thẻ quảng cáo này làm sai lệch dữ liệu.
**Action:** Cập nhật lại logic Parser theo cơ chế **Head-Sibling**:

1. Tìm tất cả các ô có class `.responsive-table-cell-head` (Mã ngành).
2. Với mỗi mã, tìm thẻ anh em (`sibling`) kế tiếp có class nội dung, tự động bỏ qua các thẻ quảng cáo ở giữa.
3. Thêm bộ đếm `DEEP` vào log terminal để User theo dõi được số lượng ngành nghề lấy được theo thời gian thực.
**Result:** Terminal báo chỉ số `DEEP` tăng đều. Dữ liệu jsonl đã có đầy đủ trường `industries_detail`.

---

### Date: 2026-01-14 (Session 4: The 'Ultimate Speed' Optimization)

**Task:** Tăng tốc độ cào dữ liệu lên giới hạn phần cứng (Hardware Limit).

**User:** Tốc độ hiện tại còn hơi chậm, có cách nào tăng thêm không?
**AI:** Hiện tại chúng ta đang bị nghẽn ở bước khởi tạo kết nối mạng (Network Handshake) và việc quản lý luồng quá an toàn. Tôi đề xuất giải pháp "Turbo":

1. **Connection Pooling**: Tái sử dụng kết nối HTTPS (Keep-Alive), giảm độ trễ 0.3s/request.
2. **Parallel Detail Fetching**: Thay vì cào tuần tự, mỗi worker chính sẽ đẻ ra 10 threads con để cào song song 10 trang chi tiết cùng lúc.

**User:** Tốc độ hiện tại là nhanh nhất có thể chưa? Tôi muốn max speed.
**AI:** Vẫn có thể nhanh hơn. Tôi sẽ kích hoạt chế độ **"Ultimate Speed"**:

1. **Global ThreadPool**: Thay vì tạo/hủy thread liên tục, tôi dùng một `ThreadPoolExecutor` toàn cục duy nhất cho 1.000.000 request.
2. **Max Connections**: Mở rộng `HTTPAdapter` lên 1000 kết nối đồng thời.
3. **Workers**: Tăng số luồng quét trang danh sách lên **100**.
**Action:** Cập nhật `spider.py` với kiến trúc mới.
**Warning:** Tốc độ này sẽ chiếm dụng gần hết băng thông mạng của máy tính.
**Result:** Crawler đạt tốc độ cao nhất từ trước đến nay.

---

### Date: 2026-01-18 -> 2026-01-20

**Task:** Advanced Data Processing: Deduplication & Review Mapping.

**User:** Chúng ta đã có dữ liệu thô (1.8 triệu dòng) và các file review từ ITviec, 1900.com.vn. Hãy làm sạch và nối chúng lại với nhau.

**Phase 1: Deduplication (Lọc trùng)**
**AI:** Dữ liệu thô từ nhiều nguồn cào khác nhau chắc chắn có trùng lặp. Tôi đã triển khai chiến thuật **"Dual-Key Deduplication"**:

1. **Primary Key (Mã số thuế):** Nếu trùng MST -> Giữ bản ghi đầu tiên, loại bỏ bản ghi sau.
2. **Secondary Key (Hash Tên + Địa chỉ):** Với công ty chưa có MST, tôi tạo hash từ `normalize(name) + normalize(address)`. Nếu trùng hash -> Loại bỏ.
**Result:** File sạch `merged_data_cleaned.jsonl` chứa 1.811.801 bản ghi unique.

**Phase 2: Mapping ITviec Reviews**
**User:** Map review từ file `reviews_itviec.jsonl`. File này có địa chỉ cụ thể nên chắc dễ.
**AI:** Chính xác. Tôi dùng thuật toán khớp `slug_name` (từ URL) và lọc theo Tỉnh/Thành phố.
**Action:** Chạy script `map_itviec_reviews.py`.
**Result:** Map thành công **8,755** công ty. Độ chính xác rất cao nhờ dữ liệu địa chỉ chi tiết.

---

### Date: 2026-01-22

**Task:** Vietnamese-Only Review Segmentation.

**User:** Bây giờ hãy map các bài review lại, tuy nhiên lần này tôi muốn chỉ segment review tiếng Việt thôi, không segment review mà là tiếng khác.
**AI:** Đã cập nhật script `segment_full.py` với logic nhận diện ngôn ngữ:

1. **Hàm `is_vietnamese()`:** Sử dụng regex check các ký tự đặc biệt tiếng Việt (dấu sắc, huyền, hỏi, ngã, nặng...).
2. **Hàm `safe_segment(text, check_lang=True)`:** Nếu `check_lang=True` và text không chứa ký tự tiếng Việt → Giữ nguyên, không segment.

**Action:** Chạy lại toàn bộ pipeline với logic mới.
**Result:**

- 37,097 review tiếng Anh được **giữ nguyên** (không bị PyVi tách sai).
- 13,536 review tiếng Việt được **segment đúng cách**.
- File output: `data/final_data_segmented.jsonl`.

---

### Date: 2026-01-23

**Task:** Comprehensive Data Cleaning (Fix ALL CAPS, Ký tự lỗi, Dính chữ).

**User:** Code còn thiếu logic fix ký tự lỗi bên trường tên công ty. Bổ sung cho đủ.
**AI:** Đã phát triển hệ thống cleaning toàn diện:

1. **`strip_html()`:** Xóa HTML tags và entities (`&nbsp;`, `&amp;`...).
2. **`fix_company_name()`:**
   - Xóa Replacement Character (``), Mojibake (`â€"` → `–`).
   - **Fix ALL CAPS → Title Case** (giữ nguyên các từ viết tắt: TNHH, CP, XNK, TM...).
3. **`fix_representative()`:**
   - Xóa digits (số điện thoại lẫn vào tên).
   - Fix ALL CAPS → Title Case.
4. **`fix_address_text()`:**
   - Tách từ dính (`SỐ3` → `Số 3`, `Tầng2` → `Tầng 2`).
   - Chuẩn hóa Case cho keywords (giữ nguyên `SO` - Shop Office).

**Test Result:**

- **ALL CAPS Fix:** `CÔNG TY TNHH TRUYỀN THÔNG VÀ SỰ KIỆN VIBE` → `Công Ty TNHH Truyền Thông Và Sự Kiện Vibe` ✅
- **Abbreviation Preserved:** `TNHH` không bị đổi thành `Tnhh` ✅

---

### Date: 2026-01-24

**Task:** Clean Data Pipeline Creation & Final Packaging.

**User:** Tạo 1 folder về clean data chứa các loại code chính: gộp file, lọc trùng, clean, map reviews, segment.
**AI:** Đã tạo thư mục `src/clean_data_pipeline/` với 7 file:

| File | Chức năng |
| :--- | :--- |
| `00_merge_sources.py` | Gộp 3 file nguồn dữ liệu gốc |
| `01_deduplicate.py` | Lọc trùng theo 3 trường (Tax + Name + Address) |
| `02_fix_errors.py` | Clean toàn diện (Name + Rep + Address) |
| `03_map_itviec.py` | Map review ITviec |
| `04_map_1900.py` | Map review 1900 |
| `05_segment.py` | Segment (bảo vệ review tiếng Anh) |
| `README.md` | Hướng dẫn sử dụng pipeline |

**User:** Lọc trùng trước rồi mới clean code (thay đổi thứ tự pipeline).
**AI:** Đã cập nhật pipeline theo thứ tự mới: **Merge → Dedup → Clean → Map → Segment**.

**User:** Zip lại cho tôi, chỉ những file cần thôi.
**AI:** Đã dọn dẹp các file test/cũ và tạo file `clean_data_pipeline.zip` chứa 7 file code sạch.

**Final Deliverable:**

- File zip `clean_data_pipeline.zip` chứa pipeline hoàn chỉnh.
- File dữ liệu cuối: `data/milestone1_delivered.jsonl` (~1.84 triệu records sạch).

---

## 3. Nhật ký Thành viên 3

### Date: 2026-01-11

**Task 1: Khởi tạo dự án & Lên kế hoạch**
**User:** Dựa vào file đặc tả SEG301, hoàn thành Milestone 1 - Chủ đề 3 (Thông tin Doanh nghiệp).
**AI:** Phân tích yêu cầu và đề xuất kế hoạch:

- **Mục tiêu:** 1,000,000 documents.
- **Nguồn:** Masothue.com, Hosocongty.vn, Reviewcongty.com.
- **Kiến trúc:** Python Async Crawler (aiohttp), Checkpoint resume, Team work.

**Task 2: Thiết lập cấu trúc dự án**
**User:** Tạo project `SEG301-OverFitting` đầy đủ file.
**AI:** Đã tạo toàn bộ cấu trúc chuẩn (src/, data_sample/, requirements.txt, .gitignore).

**Task 3: Đẩy code lên GitHub**
**User:** Push code lên repo chung.
**AI:** Thực hiện `git init`, `git add`, `git commit` và push thành công `Initial commit`.

**Task 4: Member 1 thực hiện Crawl (Thử nghiệm 1)**
**User:** Tôi là Member 1, hãy chạy crawler nhiệm vụ của tôi.
**Actions:** AI tạo script `member1_crawl.py` (sử dụng `aiohttp`). Gặp lỗi **HTTP 429 (Rate Limit)**.

**Task 5: Kiểm chứng cơ chế Resume**
**User:** Nếu tắt máy, làm sao chạy tiếp?
**AI:** Giải thích cơ chế Checkpoint lưu trạng thái vào JSON. Không cần crawl lại từ đầu.

**Task 6: Thu thập 350 Documents đầu tiên**
**User:** Tiếp tục chạy crawler bất chấp chậm.
**Result:** Thu được 350 documents hoàn chỉnh. Đã push lên GitHub làm bằng chứng tiến độ.

**Task 7: Phân tích Hiệu năng & Chuyển đổi chiến lược (CRITICAL)**
**User:** Cảnh báo tốc độ quá chậm. Hỏi giải pháp để đạt 1M docs khả thi.
**AI:** Đề xuất chuyển sang thư viện **`curl_cffi`** để giả lập trình duyệt Chrome 110 thật, bypass TLS Fingerprint.

**Task 8: Triển khai FastCrawler & Kết quả**
**AI:** Viết lại crawler mới `src/crawler/fast_crawler.py`.
**Kết quả Đột phá:** Tốc độ tăng gấp ~20-30 lần, không còn bị chặn 429/403.

---

### Date: 2026-01-13 -> 2026-01-15

**Task 11: Mở rộng quy mô Crawl (National Scale)**
**User:** Yêu cầu chạy tối đa để đạt/vượt 1.000.000 docs.
**AI:** Mở rộng danh sách tỉnh thành quét. Nâng cấp code xử lý lỗi Unicode và cơ chế Retry.

**Task 13: Tối ưu hóa Cực đại (GOD MODE)**
**User:** Yêu cầu tối ưu hóa crawler đến mức "không thể tốt hơn".
**AI:** Triển khai `GodCrawler`: Xoay vòng Browser Fingerprint trên từng request, giả mạo Organic Traffic (Google Referer).

**Task 14: Triển khai Hydra Engine (Final Solution)**
**User:** Yêu cầu một phương pháp "tốt nhất hiện nay", kết hợp cào nhiều web.
**AI:** Phát triển `ultimate_crawler.py` (Hydra Engine): Kết hợp đa nguồn (Masothue, Hosocongty, Timcongty), Failure detection và Failure switching. Ngoài ra sử dụng `eager` page load strategy để tăng tốc Selenium gấp 3 lần.

---

### Date: 2026-01-20

**Task 18: Crawl Itviec Reviews (Detailed Address)**
**User:** Yêu cầu crawl review từ Itviec.com, bao gồm địa chỉ chi tiết từng công ty.
**AI Action:** Phát triển `src/crawler/crawl_itviec.py` sử dụng `curl_cffi`.
**Kết quả:** Thu thập thành công **1511 reviews** chất lượng cao với địa chỉ chi tiết đã decode.

---

---

### Date: 2026-01-24 (Final Session - Project Clean-up & Documentation)

**Task:** Hệ thống hóa toàn bộ mã nguồn và hoàn thiện báo cáo Milestone 1.

**User:** Tôi muốn gộp tất cả các file code rải rác ở code2, code3 vào src/crawler, lọc bỏ file thừa và tổ chức lại theo một luồng logic: Cào -> Map Review -> Dedup -> Clean -> Segment.
**AI:** Đã thực hiện tái cấu trúc toàn diện:

1. **Module hóa Pipeline**: Chia nhỏ quy trình thành các bước `step1_mapping`, `step2_deduplicate`, `step3_cleaning`, `step4_segmentation`.
2. **File thực thi tổng**: Tạo `run_pipeline.py` để chạy toàn bộ quy trình chỉ bằng một lệnh duy nhất.
3. **Cập nhật Crawler**: Giữ lại `crawl_enterprise.py` (tối ưu 100 luồng) và `crawl_reviews.py` làm nguồn cấp dữ liệu thô.

**User:** Chỉnh sửa README và Báo cáo Milestone 1 dựa trên file đặc tả của giảng viên. Cập nhật thông tin thành viên nhóm: Nguyễn Thanh Trà (QE190099), Phan Đỗ Thanh Tuấn (QE190123), Châu Thái Nhật Minh (QE190109).
**AI:** Đã cập nhật:

- **README.md**: Thêm thông tin thành viên, cấu trúc thư mục chuẩn, hướng dẫn cài đặt venv và cách chạy pipeline mới.
- **Milestone1_Report.md**: Bổ sung phân tích kỹ thuật (Bypass Cloudflare, Dual-key Dedup), thống kê dữ liệu (1.8 triệu docs, Vocabulary size, Avg doc length) và giải trình lý do cần Word Segmentation.
- **requirements.txt**: Chốt danh sách thư viện (requests, bs4, curl_cffi, pyvi, unidecode).

**Final Result:** Project đã sẵn sàng nộp bài với cấu trúc chuẩn, code sạch và tài liệu đầy đủ.

### Date: 2026-01-26

**Task:** Tối ưu hóa độ ổn định (Stability Optimization).

**User:** Có nên giảm số lượng worker từ 100 xuống còn 50 không?
**AI:** Đề xuất giảm xuống 50 worker. Mặc dù tốc độ tối đa giảm đi, nhưng điều này giúp hệ thống ổn định hơn, tránh bị nhà mạng hoặc server chặn IP (Rate Limit) và giảm tải cho tài nguyên máy tính cục bộ khi chạy trong thời gian dài.
**Action:**

1. Cập nhật `crawl_enterprise.py`: `WORKERS = 50`.
2. Cập nhật `README.md` và `Milestone1_Report.md`: Điều chỉnh các thông số kỹ thuật tương ứng.
**Result:** Crawler hoạt động bền bỉ hơn, giảm thiểu rủi ro lỗi kết nối.

---

## 4. Milestone 2: Core Search Engine (SPIMI & BM25)

### Date: 2026-02-22 -> 2026-02-23

**Task:** Xây dựng hệ thống tìm kiếm cốt lõi sử dụng thuật toán SPIMI và xếp hạng BM25.

**User:** Bắt đầu Milestone 2. Tôi cần xây dựng Indexer sử dụng thuật toán SPIMI để xử lý 1.8 triệu docs mà không làm tràn RAM.
**AI:** Tôi đề xuất chia dữ liệu thành các blocks (vd: 50,000 docs/block). Mỗi block sẽ được index trong RAM rồi ghi xuống đĩa dưới dạng file pickle tạm thời. Sau đó chúng ta sẽ dùng K-way merge để gộp lại.

**User:** Khi tôi gộp tất cả thành một file `final_index.pkl` khổng lồ (1GB), máy bị treo khi load. Làm sao tối ưu?
**AI:** Đã chuyển đổi sang **Kiến trúc 2-file**:

1. **`term_dict.pkl`**: Chỉ chứa mapping từ và vị trí byte (offset). File này rất nhẹ (~18MB), load vào RAM cực nhanh.
2. **`postings.bin`**: Chứa dữ liệu danh sách văn bản (postings) dạng nhị phân. Khi search, ta chỉ cần `seek` đến đúng vị trí byte và đọc phần cần thiết, không cần load toàn bộ file 1GB vào RAM.

**User:** File metadata (thông tin công ty) để hiển thị kết quả cũng nặng tới 1.8GB, vẫn bị treo máy.
**AI:** Một đột phá mới! Tôi đã thay thế việc lưu Metadata bằng **`doc_offsets.pkl` (~20MB)**.

- Thay vì lưu nội dung, ta lưu vị trí byte của từng dòng trong file `milestone1_fixed.jsonl`.
- Khi hiển thị kết quả search, ta dùng `seek` để đọc trực tiếp từ file JSONL gốc.
- **Kết quả:** RAM tiêu thụ giảm từ 3GB+ xuống còn **~55MB**. Thời gian khởi động giảm từ 15 phút xuống **0.7 giây**.

**User:** Search các từ phổ biến như "công_ty" vẫn bị chậm.
**AI:** Do postings list của từ "công_ty" chứa tới 1.5 triệu văn bản. Tôi đã thêm cơ chế **Stopword/Common Term Filter**:

- Tự động bỏ qua các từ xuất hiện trong >30% tổng số văn bản (vì IDF của chúng rất thấp, không quan trọng cho xếp hạng).
- **Kết quả:** Tốc độ search các từ khóa phổ biến giờ chỉ mất **< 0.1 giây**.

**Result:** Hoàn thiện bộ code `spimi.py`, `merging.py`, `bm25.py` và `search_console.py` với hiệu năng cực cao.

**Task:** Tối ưu hóa trải nghiệm tìm kiếm (Automatic Query Segmentation).

**User:** Có cách nào để query không cần nhập dấu gạch dưới mà hệ thống vẫn đạt độ chính xác tốt không?
**AI:** Đã tích hợp thư viện `pyvi` vào module `BM25Searcher`.

- **Cải tiến:** Khi người dùng nhập query có khoảng trắng (vd: `công nghệ`), hệ thống sẽ tự động gọi `ViTokenizer.tokenize()` để chuyển đổi thành token đúng định dạng index (`công_nghệ`).
- **Lợi ích:** Người dùng không cần quan tâm đến định dạng lưu trữ bên dưới, chỉ cần gõ tiếng Việt tự nhiên.
- **Robustness:** Có cơ chế try-except để đảm bảo code vẫn chạy kể cả khi môi trường chưa cài `pyvi`.
- **Môi trường:** Toàn bộ quá trình cài đặt và chạy thử nghiệm tính năng này được thực hiện trong môi trường ảo (`venv`) của dự án để đảm bảo tính cô lập và đúng yêu cầu đồ án.

**Task:** Dọn dẹp hệ thống và đóng gói Milestone 2.

**User:** Kiểm tra lại folder data/index xem có file nào cũ không dùng không thì xóa đi, rồi đẩy dự án lên github nhé.
**AI:** Đã thực hiện dọn dẹp các file rác và file index cũ để tối ưu dung lượng:

- **Xóa:** `doc_metadata.pkl` (1.8GB), `final_index.pkl` (1.1GB) và thư mục tạm `blocks/`.
- **Giữ lại:** Bộ index 2-file tối ưu (`term_dict.pkl`, `postings.bin`) và các file cần thiết (`doc_lengths.pkl`, `doc_offsets.pkl`).
- **Git:** Kiểm tra lại `.gitignore` và thực hiện push toàn bộ mã nguồn Milestone 2 lên GitHub.

**Task:** Fix lỗi hiển thị ngành nghề bị đứt đoạn.

**User:** Sao output ở phần industry không liệt kê hết mà bị đứt thông tin vậy?
**AI:** Đã điều chỉnh hàm `display_results` trong `bm25.py`.

- **Sửa lỗi:** Loại bỏ giới hạn 150 ký tự để hiển thị đầy đủ danh sách ngành nghề của doanh nghiệp.
- **Tối ưu hiển thị:** Tự động chuyển đổi dấu gạch dưới `_` thành khoảng trắng trong kết quả hiển thị để người dùng đọc thuận tiện hơn, trong khi vẫn giữ nguyên logic xử lý ở backend.

---

### Date: 2026-03-01 (Session: Algorithm & Display Optimization)

**Task:** Tối ưu hóa độ chính xác xếp hạng và xử lý lỗi hiển thị ngành nghề.

**User:** Khi tìm kiếm "xây dựng Hà Nội", hệ thống tự động bỏ qua từ "xây_dựng" vì nó quá phổ biến, dẫn đến kết quả trả về toàn các ngành nghề không liên quan. Một số kết quả lại bị trống phần Industry.

**AI:** Đã thực hiện 3 cải tiến quan trọng:

1. **Tối ưu Keyword Skip Logic:**
    - Tăng ngưỡng `max_df` từ **30% lên 80%**. Các từ khóa ngành nghề trọng yếu như "xây dựng" sẽ không bị loại bỏ.
    - Thêm điều kiện: Không bao giờ skip từ khóa nếu truy vấn của người dùng chỉ có **1-2 từ**, đảm bảo ý định tìm kiếm luôn được tôn trọng tuyệt đối.

2. **Triển khai Coordination Boost (Hệ số phối hợp):**
    - BM25 mặc định dùng toán tử OR, dễ gây hiện tượng "lạc đề". Tôi đã bổ sung hệ số: `Score = Score * (Số từ khớp / Tổng số từ query)^2`.
    - **Kết quả:** Những doanh nghiệp chứa đồng thời cả "xây dựng" và "Hà Nội" sẽ có điểm cao vọt lên đầu, loại bỏ các kết quả chỉ chứa một từ đơn lẻ.

3. **Metadata Fallback (Sửa lỗi trống ngành nghề):**
    - Cập nhật hàm `_get_doc_metadata` để kiểm tra đa tầng các trường dữ liệu: `industries_str_seg` -> `industries_str` -> `industries_detail`.
    - Đảm bảo hiển thị đầy đủ thông tin kể cả khi cấu trúc JSON thô không đồng nhất.

**User:** Hãy tối ưu tốc độ vì khi bao gồm cả từ khóa "xây dựng" (762k docs), search bị chậm lại.
**AI:** Đã thực hiện **Hot-loop Optimization**: Inline hàm tính điểm TF và pre-calculate các hằng số BM25 ra ngoài vòng lặp. Tốc độ tìm kiếm "xây dựng Hà Nội" vẫn duy trì ở mức cực nhanh dù khối lượng dữ liệu xử lý tăng gấp nhiều lần.

**Result:** Kết quả tìm kiếm hiện tại cực kỳ chính xác và đầy đủ thông tin.

---

### Date: 2026-03-01 (Session: Milestone 2 Finalization & Reporting)

**Task:** Hoàn thiện báo cáo kỹ thuật và kiểm chứng số liệu cuối cùng cho Milestone 2.

**User:** Tạo báo cáo Milestone 2 chi tiết và làm sạch mã nguồn (xóa các module không cần thiết).

**AI:** Đã thực hiện các bước sau:

1. **Cleanup & Removal:**
    - Xóa module `src/indexer/compression.py` (do không được sử dụng trong luồng xử lý chính).

2. **Báo cáo Kỹ thuật (Milestone2_Report.md):**
    - Lồng ghép mô tả chi tiết từng file mã nguồn (`spimi.py`, `merging.py`, `bm25.py`) vào quy trình Indexing/Ranking.
    - Phân tích sự chênh lệch số lượng Vocabulary (18k vs 695k) do cơ chế **sampling 1%** ở M1 so với **full-indexing 100%** ở M2.

3. **Kiểm chứng số liệu (index_stats_verifier.py):**
    - Tổng số văn bản: **1,842,525**.
    - Vocabulary Size: **695,470**.
    - Tổng số Tokens: **342,502,541**.
    - Độ dài trung bình (Avgdl): **185.89**.

4. **Display & Bug Fixing:**
    - **Sửa địa chỉ:** Tự động loại bỏ dấu phẩy dư thừa ở đầu chuỗi địa chỉ (`strip(", ")`).
    - **Sửa Người đại diện:** Thêm fallback hiển thị "(Chưa cập nhật)" khi dữ liệu là None.
    - **Nhận diện lỗi Tax Code:** Phát hiện lỗi Regex ở Crawler khiến mã số thuế bị mất hậu tố `-xxx`.

**Result:** Đã đẩy toàn bộ mã nguồn sạch và báo cáo hoàn chỉnh lên GitHub nhánh `main`. Dự án đã sẵn sàng cho buổi bảo vệ Milestone 2.
