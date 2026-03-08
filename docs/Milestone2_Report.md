# BÁO CÁO MILESTONE 2: XÂY DỰNG HỆ THỐNG TÌM KIẾM THÔNG TIN DOANH NGHIỆP

**Môn học**: SEG301
**Nhóm**: OverFitting
**Thành viên**:

- Nguyễn Thanh Trà – QE190099
- Phan Đỗ Thanh Tuấn – QE190123
- Châu Thái Nhật Minh – QE190109

---

## MỤC LỤC

1. [Tổng quan & Mục tiêu Milestone 2](#1-tổng-quan--mục-tiêu-milestone-2)
2. [Quy mô & Đặc điểm Tập dữ liệu](#2-quy-mô--đặc-điểm-tập-dữ-liệu)
3. [Kiến trúc Tổng thể Hệ thống](#3-kiến-trúc-tổng-thể-hệ-thống)
4. [Thuật toán SPIMI – Lập chỉ mục theo khối](#4-thuật-toán-spimi--lập-chỉ-mục-theo-khối)
5. [Thuật toán Merge – K-way Merge Blocks](#5-thuật-toán-merge--k-way-merge-blocks)
6. [Cấu trúc Inverted Index hoàn chỉnh](#6-cấu-trúc-inverted-index-hoàn-chỉnh)
7. [Thuật toán Ranking BM25 – Triển khai thủ công](#7-thuật-toán-ranking-bm25--triển-khai-thủ-công)
8. [Tối ưu hóa Bộ nhớ & Tốc độ](#8-tối-ưu-hóa-bộ-nhớ--tốc-độ)
9. [Giao diện Console Search](#9-giao-diện-console-search)
10. [Kết quả thực tế & Số liệu đo lường](#10-kết-quả-thực-tế--số-liệu-đo-lường)

---

## 1. Tổng quan & Mục tiêu Milestone 2

### 1.1. Mục tiêu

Milestone 2 là giai đoạn **cốt lõi** của dự án: biến bộ dữ liệu 1.8 triệu doanh nghiệp (đã thu thập ở Milestone 1) thành một **công cụ tìm kiếm**. Người dùng có thể gõ từ khóa bất kỳ và nhận về Top 10 doanh nghiệp phù hợp nhất trong **< 1 giây**.

Mục tiêu cụ thể:

- Xây dựng **Inverted Index** hiệu quả từ 1.8 triệu tài liệu, không làm treo máy.
- Triển khai **thuật toán ranking BM25** hoàn toàn thủ công (không dùng thư viện sẵn).
- Đảm bảo **tốc độ tìm kiếm < 1 giây** cho mỗi truy vấn.
- Tối ưu để **RAM khi chạy search < 100MB** (thay vì hàng GB nếu load toàn bộ index).

### 1.2. Nguyên tắc xây dựng

Nhóm tự cài đặt toàn bộ các thuật toán (SPIMI, K-way Merge, BM25) từ code Python thuần, không sử dụng bất kỳ thư viện search engine nào có sẵn.

---

## 2. Quy mô & Đặc điểm Tập dữ liệu

### 2.1. Thống kê tổng quát

| Thông số | Giá trị |
|---|---|
| Số lượng tài liệu (documents) | **1.842.525 doanh nghiệp** |
| Kích thước file dữ liệu thô | **~6.2 GB** (định dạng JSONL) |
| Tổng số token sau indexing | **342.502.541 tokens** |
| Vocabulary (từ vựng duy nhất) | **695.470 terms** |

### 2.2. Cấu trúc mỗi tài liệu (document)

Mỗi dòng trong file JSONL là một JSON object đại diện cho một doanh nghiệp, gồm các trường:

```json
{
  "company_name": "Công ty TNHH ABC",
  "company_name_seg": "công_ty tnhh abc",
  "tax_code": "0123456789",
  "address": "123 Đường XYZ, Quận 1, TP.HCM",
  "address_seg": "123 đường xyz quận_1 tp hồ_chí_minh",
  "representative": "Nguyễn Văn A",
  "representative_seg": "nguyễn_văn_a",
  "status": "Đang hoạt động",
  "status_seg": "đang hoạt_động",
  "industries_str": "Xây dựng công trình kỹ thuật dân dụng khác",
  "industries_str_seg": "xây_dựng công_trình kỹ_thuật dân_dụng"
}
```

**Điểm quan trọng**: Milestone 1 đã thực hiện **Word Segmentation** (tách từ tiếng Việt) bằng thư viện `PyVi`. Các trường `_seg` chứa văn bản đã được tách từ, trong đó các từ ghép được nối bằng dấu `_` (ví dụ: `"bất_động_sản"`, `"hà_nội"`). Milestone 2 kế thừa và tận dụng trực tiếp kết quả này.

---

## 3. Kiến trúc Tổng thể Hệ thống

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PIPELINE MILESTONE 2                            │
│                                                                     │
│  [milestone1_fixed.jsonl]  ──►  [SPIMI Indexer]  ──►  [Merge]       │
│       6.2 GB dữ liệu              spimi.py             merging.py   │
│       1.8M documents              37 blocks            K-way Merge  │
│                                   (50k doc/block)                   │
│                                        │                            │
│                                        ▼                            │
│                              ┌──────────────────┐                   │
│                              │ INVERTED INDEX   │                   │
│                              │ term_dict.pkl    │ ~18 MB            │
│                              │ postings.bin     │ ~1.1 GB           │
│                              │ doc_lengths.pkl  │ ~12 MB            │
│                              │ doc_offsets.pkl  │ ~25 MB            │
│                              └────────┬─────────┘                   │
│                                       │                             │
│                              [BM25 Searcher]                        │
│                               bm25.py                               │
│                              RAM: ~55 MB (chỉ load dict nhẹ)        │
│                                       │                             │
│                              [search_console.py]                    │
│                              Giao diện dòng lệnh tương tác          │
└─────────────────────────────────────────────────────────────────────┘
```

**Luồng xử lý gồm 3 pha:**

| Pha | Tên | Script | Mục đích |
|-----|-----|--------|----------|
| **Pha 1** | SPIMI Indexing | `spimi.py` | Đọc data, chia block, tạo partial index |
| **Pha 2** | Merge | `merging.py` | Ghép tất cả block thành index hoàn chỉnh |
| **Pha 3** | Search | `bm25.py` + `search_console.py` | Xếp hạng & giao diện tìm kiếm |

---

## 4. Thuật toán SPIMI – Lập chỉ mục theo khối

### 4.1. Tại sao cần SPIMI?

Nếu thực hiện lập chỉ mục thông thường (đọc toàn bộ 1.8M documents vào RAM), bộ nhớ cần lên đến **hơn 6 GB** chỉ riêng cho dữ liệu thô. Chưa kể overhead của Python dictionary, tổng RAM cần thiết có thể vượt **15-20 GB**.

**SPIMI (Single-Pass In-Memory Indexing)** giải quyết vấn đề này bằng cách:

1. Chia toàn bộ dữ liệu thành các **block nhỏ** (50.000 documents/block).
2. Mỗi block xây dựng một **Partial Inverted Index** trong RAM.
3. Ghi partial index xuống đĩa, **giải phóng RAM** hoàn toàn trước khi sang block tiếp.
4. Cuối cùng, **merge** tất cả partial indexes thành một index hoàn chỉnh.

### 4.2. Quy trình chi tiết (file `src/indexer/spimi.py`)

```
[Đọc file JSONL]
      │
      ▼ (batch 50,000 docs)
[Trích xuất văn bản từ _seg fields]
      │  - company_name_seg (lặp 2 lần để boost TF)
      │  - address_seg
      │  - representative_seg
      │  - status_seg
      │  - industries_str_seg (lặp 2 lần để boost TF)
      │
      ▼
[Tokenize] → lọc token < 2 ký tự, lọc ký tự đặc biệt
      │
      ▼
[SPIMI-Invert] → dictionary[term][doc_id] += 1
      │
      ▼
[Sắp xếp theo alphabet] → ghi block_XXXX.pkl xuống đĩa
      │
      ▼ gc.collect() → giải phóng RAM hoàn toàn
[Lặp lại với batch tiếp theo...]
      │
      ▼ Kết thúc tất cả batch
[Lưu doc_lengths.pkl] → doc_id -> số tokens
[Lưu doc_offsets.pkl] → doc_id -> byte_offset trong JSONL
```

### 4.3. Kỹ thuật Boosting trong Indexing

Thay vì thêm trọng số riêng cho từng trường (phức tạp), nhóm áp dụng **TF Boosting** trực tiếp trong quá trình tokenize:

```python
# Tên công ty và ngành nghề được lặp 2 lần → TF nhân đôi
text_parts.append(company_name_seg)
text_parts.append(company_name_seg)   # Boost: TF × 2

text_parts.append(industries_str_seg)
text_parts.append(industries_str_seg)  # Boost: TF × 2
```

**Lý do**: Khi tìm "Công ty xây dựng ABC", kết quả có tên công ty khớp chính xác phải nổi trên kết quả chỉ có địa chỉ khớp.

### 4.4. Đọc file ở Binary Mode

```python
# Sử dụng binary mode thay vì text mode
with open(jsonl_path, "rb") as f:
    byte_offset = f.tell()  # Ghi nhớ vị trí byte
    raw_line = f.readline()
```

**Lý do**: Trên Windows, đọc file text với `tell()` rất chậm do Python phải theo dõi từng ký tự UTF-8. Đọc binary mode cho `tell()` chính xác và nhanh hơn.

### 4.5. Kết quả Pha 1

| Thông số | Giá trị |
|---|---|
| Số block tạo ra | 37 blocks |
| Documents mỗi block | 50.000 |

---

## 5. Thuật toán Merge – K-way Merge Blocks

### 5.1. Vấn đề cần giải quyết

Sau Pha 1, ta có **37 file block** trên đĩa, mỗi file là một Partial Inverted Index đã sắp xếp theo alphabet. Cùng một term (ví dụ: `"hà_nội"`) có thể xuất hiện trong nhiều block khác nhau với postings list khác nhau. Mục tiêu: **Ghép tất cả lại thành một index duy nhất**.

### 5.2. Thuật toán K-way Merge với Min-Heap

Nhóm triển khai **K-way merge** – giống thuật toán MergeSort nhưng cho K dãy đã sắp xếp:

```
Block 0: [abc, bất_động_sản, công_ty, ...]
Block 1: [abc, dịch_vụ, hà_nội, ...]
Block 2: [bất_động_sản, công_ty, giáo_dục, ...]
...

            ┌──────────────────────────────┐
            │     Min-Heap (Priority Queue)│
            │  (term, block_id) tuples     │
            └──────────────┬───────────────┘
                           │
          Pop term nhỏ nhất (abc từ Block 0)
                           │  
          Gom tất cả postings của "abc" từ MỌI block
                           │
          Merge & sort postings theo doc_id
                           │
          Ghi vào postings.bin, lưu offset vào term_dict
                           │
          Push term_tiếp_theo của Block 0 vào Heap
```

### 5.3. Class `BlockReader` – Trái tim của Merge

```python
class BlockReader:
    def open(self): 
        # Load toàn bộ block từ pickle vào RAM
        # Tạo iterator theo thứ tự alphabet
    
    def current_term -> str:
        # Term đang được trỏ tới
    
    def current_postings -> List[(doc_id, tf)]:
        # Postings list của term hiện tại
    
    def consume():
        # Tiêu thụ term này, chuyển sang term tiếp theo
```

### 5.4. Kiến trúc 2-File Index

Thay vì lưu tất cả vào 1 file khổng lồ, nhóm phân tách thành 2 file:

```
┌─────────────────────────────────────────────────────┐
│  term_dict.pkl (~18 MB) – Load toàn bộ vào RAM      │
│  {"hà_nội": (df=950000, offset=0x1A2B3C, length=N)  │
│   "xây_dựng": (df=430000, offset=0x5F6G7H, length=M)│
│   ... 695,470 terms ... }                           │
└─────────────────────────────────────────────────────┘
          │
          │ Dùng offset để seek() trực tiếp
          ▼
┌─────────────────────────────────────────────────────┐
│  postings.bin (~1.1 GB) – KHÔNG load vào RAM        │
│  Binary data chứa [(doc_id, tf), ...] pickled       │
│  Offset 0x1A2B3C: [(doc1, 3), (doc5, 1), ...]       │
│  Offset 0x5F6G7H: [(doc2, 5), (doc8, 2), ...]       │
│  ...                                                │
└─────────────────────────────────────────────────────┘
```

**Lợi ích thiết kế này:**

- Khi search, chỉ cần **load `term_dict.pkl` (~18MB)** vào RAM.
- Postings cho từng term được **đọc theo yêu cầu (on-demand)** bằng `file.seek(offset)` – O(1).
- Tiết kiệm hàng GB RAM so với load toàn bộ index.

---

## 6. Cấu trúc Inverted Index hoàn chỉnh

### 6.1. Bốn file cấu thành index

Sau khi hoàn thành 2 pha, thư mục `data/index/` chứa 4 file:

```
data/index/
├── term_dict.pkl    (~18 MB)   – "Bảng tra cứu từ điển"
├── postings.bin     (~1.1 GB)  – "Kho dữ liệu posting"
├── doc_lengths.pkl  (~12 MB)   – "Độ dài mỗi tài liệu"
└── doc_offsets.pkl  (~25 MB)   – "Bản đồ vị trí trong JSONL"
```

### 6.2. Chi tiết từng file

**`term_dict.pkl`**  
Dictionary Python: `{ term: (df, byte_offset, byte_length) }`

- `df` (document frequency): Số tài liệu chứa term này.
- `byte_offset`: Vị trí bắt đầu của postings trong `postings.bin`.
- `byte_length`: Độ dài (bytes) của postings để đọc đúng chunk.

**`postings.bin`**  
Binary file, mỗi entry là kết quả `pickle.dumps([(doc_id, tf), ...])`.

- Đọc bằng `f.seek(offset)` rồi `f.read(length)`, sau đó `pickle.loads()`.
- Đây là file lớn nhất (~1.1 GB) nhưng **không bao giờ được load toàn bộ**.

**`doc_lengths.pkl`**  
Dictionary: `{ doc_id: length }` (length = số tokens của tài liệu đó).  
Cần thiết để tính **document length normalization** trong BM25.

**`doc_offsets.pkl`**  
Dictionary: `{ doc_id: byte_offset }` (byte_offset trong file JSONL gốc).  
Cho phép đọc metadata của bất kỳ doanh nghiệp nào trực tiếp từ file 6.2 GB mà **không cần scan từ đầu**.

---

## 7. Thuật toán Ranking BM25 – Triển khai thủ công

### 7.1. Công thức BM25

$$\text{score}(D, Q) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \frac{tf(q_i, D) \cdot (k_1 + 1)}{tf(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{avgdl}\right)}$$

**Giải thích từng thành phần:**

| Ký hiệu | Ý nghĩa | Giá trị trong hệ thống |
|---------|---------|----------------------|
| `IDF(qi)` | Inverse Document Frequency – đo mức độ "hiếm" của term | Tính theo công thức Robertson-Sparck Jones |
| `tf(qi, D)` | Số lần term `qi` xuất hiện trong document `D` | Lấy từ postings list |
| `k1` | Term frequency saturation – giới hạn ảnh hưởng của TF | **1.2** (mặc định) |
| `b` | Document length normalization strength | **0.75** (mặc định) |
| `|D|` | Độ dài tài liệu D (số tokens) | Lấy từ `doc_lengths.pkl` |
| `avgdl` | Độ dài tài liệu trung bình của toàn corpus | Tính khi load index |

### 7.2. Công thức IDF (Robertson-Sparck Jones)

$$\text{IDF}(t) = \log\left(\frac{N - df(t) + 0.5}{df(t) + 0.5} + 1\right)$$

- `N` = 1.842.525 (tổng số tài liệu)
- `df(t)` = document frequency của term `t` (lấy từ `term_dict`)
- Nếu term rất phổ biến (`df` lớn) → IDF gần 0 → ít ảnh hưởng đến rank
- Nếu term rất hiếm (`df` nhỏ) → IDF lớn → ảnh hưởng mạnh đến rank

**Ví dụ thực tế:**

- `"tnhh"` xuất hiện trong ~90% corpus → IDF ≈ 0.1 (không quan trọng)
- `"spacex"` xuất hiện trong ~5 documents → IDF ≈ 12.7 (cực kỳ quan trọng)

### 7.3. Cài đặt thủ công trong Python (`src/ranking/bm25.py`)

```python
def compute_idf(self, term: str) -> float:
    df = self.term_dict[term][0]
    N = self.total_docs
    return math.log((N - df + 0.5) / (df + 0.5) + 1)

def compute_tf_component(self, tf: int, doc_length: int) -> float:
    length_norm = 1 - self.b + self.b * (doc_length / self.avg_doc_length)
    return (tf * (self.k1 + 1)) / (tf + self.k1 * length_norm)
```

### 7.4. Coordination Factor – Cải tiến quan trọng

**Vấn đề gốc của BM25 thuần túy**: Query "công ty xây dựng hà nội" (3 từ) → Một document có `tf("hà_nội") = 50` (rất cao cho một từ) có thể đánh bại document có cả 3 từ nhưng TF vừa phải.

**Giải pháp: Coordination Boost**

```python
# Đếm số query term mà mỗi document CÓ (bất kể TF)
doc_term_matches[doc_id] += 1  # mỗi term khớp

# Sau khi tính xong BM25 score:
coordination_factor = num_terms_matched / total_query_terms
doc_scores[doc_id] *= (coordination_factor ** 2)
```

**Ví dụ minh họa:**

| Document | BM25 thuần | Terms khớp | Coordination | Final Score |
|----------|-----------|-----------|--------------|-------------|
| Doc A: có "hà_nội" TF=50, thiếu 2 term kia | 8.0 | 1/3 = 0.33 | × 0.11 | **0.88** |
| Doc B: có đủ 3 terms, TF vừa phải | 5.0 | 3/3 = 1.0 | × 1.0 | **5.00** |

→ Doc B (có đủ 3 term) vượt lên trên Doc A (chỉ khớp 1 term với TF cao).

### 7.5. Skip Term quá phổ biến (Optimization)

```python
max_df = int(self.total_docs * 0.8)  # 80% corpus

if df > max_df and len(query_tokens) > 2:
    continue  # Skip term này
```

- Nếu query ngắn (1-2 từ): Không skip, tôn trọng mọi term.
- Nếu query dài (>2 từ): Skip các term quá phổ biến vì postings list của chúng có hàng triệu entries → `pickle.loads()` cực chậm, nhưng IDF lại gần 0 → đóng góp không đáng kể.

### 7.6. Quy trình Search đầy đủ

```
User nhập query: "công ty xây dựng hà nội"
          │
          ▼
[Tokenize query]
 → PyVi: "công_ty xây_dựng hà_nội"
 → Tokens: ["công_ty", "xây_dựng", "hà_nội"]
          │
          ▼
[Với mỗi token:]
 → Tra term_dict → lấy (df, offset, length)
 → Tính IDF
 → Đọc postings từ postings.bin [file.seek(offset), file.read(length), pickle.loads()]
 → Với mỗi (doc_id, tf) trong postings:
     doc_scores[doc_id] += IDF × TF_BM25_component
     doc_term_matches[doc_id] += 1
          │
          ▼
[Áp dụng Coordination Factor]
 doc_scores[doc_id] *= (matches/total_query_terms)^2
          │
          ▼
[Sort by score → lấy Top-K]
          │
          ▼
[Đọc metadata on-demand từ JSONL]
 → doc_offsets[doc_id] → byte_offset
 → jsonl_file.seek(byte_offset) → readline() → json.loads()
          │
          ▼
[Trả về kết quả cho user]
  Tổng thời gian: < 500ms
```

---

## 8. Tối ưu hóa Bộ nhớ & Tốc độ

### 8.1. Chiến lược quản lý RAM

Đây là thách thức kỹ thuật lớn nhất của Milestone 2. Nhóm áp dụng 3 lớp tối ưu:

#### Lớp 1: SPIMI Chunked Indexing

- Không bao giờ load toàn bộ 6.2 GB vào RAM.
- Chỉ giữ 50.000 documents (< 1 GB) trong RAM tại một thời điểm.
- `gc.collect()` sau mỗi block để giải phóng triệt để.

#### Lớp 2: 2-File Index Architecture

| Thành phần | Cách xử lý | RAM chiếm |
|-----------|-----------|-----------|
| `term_dict.pkl` | Load toàn bộ | ~18 MB |
| `postings.bin` | Random access (seek) | ~0 MB (chỉ buffer OS) |
| `doc_lengths.pkl` | Load toàn bộ | ~12 MB |
| `doc_offsets.pkl` | Load toàn bộ | ~25 MB |
| **Tổng** | | **~55 MB** |

#### Lớp 3: On-Demand Metadata

- Thông tin chi tiết (địa chỉ, ngành nghề) của từng công ty **chỉ được đọc khi user thực sự nhìn thấy kết quả**.
- Sử dụng `file.seek(byte_offset)` để nhảy thẳng đến vị trí cần đọc trong file JSONL 6.2 GB.
- Không cache metadata vào RAM → tiết kiệm hàng trăm MB.

### 8.2. Tối ưu Hot-Loop BM25

Phần tính điểm BM25 là vòng lặp chạy qua **hàng triệu (doc_id, tf) pairs**. Nhóm áp dụng **loop inlining**:

```python
# TRƯỚC (chậm hơn): gọi function mỗi lần
for doc_id, tf in postings:
    score = idf * self.compute_tf_component(tf, self.doc_lengths[doc_id])
    doc_scores[doc_id] += score

# SAU (nhanh hơn): precompute constants, inline cách tính
k1 = self.k1       # Tránh attribute lookup trong loop
b = self.b
avgdl = self.avg_doc_length
k1_plus_1 = k1 + 1  # Tính sẵn 1 lần

for doc_id, tf in postings:
    doc_length = doc_lengths.get(doc_id, avgdl)
    length_norm = 1 - b + b * (doc_length / avgdl)
    tf_comp = (tf * k1_plus_1) / (tf + k1 * length_norm)
    doc_scores[doc_id] += idf * tf_comp
```

Mức tăng tốc: ~15-20% nhanh hơn khi postings list có nhiều triệu entries.

### 8.3. Binary Mode vs Text Mode

| Chế độ đọc | Tốc độ `tell()` | Lý do |
|-----------|----------------|-------|
| Text mode (UTF-8, Windows) | Chậm (~0.8 GB/phút) | Python theo dõi từng ký tự UTF-8 |
| **Binary mode** | **Nhanh (~5 GB/phút)** | OS-level file pointer, không decode |

---

## 9. Giao diện Console Search

### 9.1. Cách sử dụng

```bash
# Bước 1: Tạo index (chỉ cần chạy 1 lần)
python src/indexer/spimi.py
python src/indexer/merging.py

# Bước 2: Tìm kiếm tương tác
python src/search_console.py
```

### 9.2. Tính năng giao diện

Khi khởi động, hệ thống hiển thị banner ASCII art và load index vào RAM (~55 MB, vài giây):

```
╔══════════════════════════════════════════════════════════════════════════════╗
║   SEG301 - Vietnamese Enterprise Search Engine                               ║
║   Milestone 2: SPIMI + BM25 | Team OverFitting                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
✅ Sẵn sàng! 1,842,525 docs | 695,470 terms
```

**Các lệnh hỗ trợ:**

| Lệnh | Chức năng |
|------|-----------|
| `[từ khóa]` | Tìm kiếm, trả về Top-10 mặc định |
| `:top N` | Đặt số kết quả (N từ 1-100) |
| `:stats` | Xem thống kê index (vocab, avgdl, BM25 params) |
| `:help` | Hướng dẫn sử dụng |
| `:quit` | Thoát chương trình |

### 9.3. Định dạng kết quả

```
  #1 [Score: 12.4561] (Doc ID: 832041)
  ├─ Company:  Công ty TNHH Xây Dựng Nam Đà Nghệ
  ├─ Tax Code: 2900827851
  ├─ Address:  Xã Nghi Trung, Huyện Nghi Lộc, Tỉnh Nghệ An
  ├─ Rep:      Nguyễn Thị Nam Đà
  ├─ Status:   Đang hoạt động
  └─ Industry: xây dựng công trình kỹ thuật dân dụng khác
```

---

## PHỤ LỤC: Cấu trúc Project

```
SEG301-OverFitting/
├── src/
│   ├── indexer/
│   │   ├── spimi.py        # SPIMI Indexing (Phase 1)
│   │   └── merging.py      # K-way Merge (Phase 2)
│   ├── ranking/
│   │   └── bm25.py         # BM25 Searcher + Display Utils
│   └── search_console.py   # Interactive Console App
├── data/
│   ├── milestone1_fixed.jsonl  # ~6.2 GB (gitignored)
│   └── index/
│       ├── term_dict.pkl        # ~18 MB
│       ├── postings.bin         # ~1.1 GB
│       ├── doc_lengths.pkl      # ~12 MB
│       ├── doc_offsets.pkl      # ~25 MB
│       └── blocks/              # 37 block files (tạm, có thể xóa sau merge)
├── docs/
│   ├── Milestone1_Report.md
│   └── Milestone2_Report.md    # (file này)
├── tests/
├── requirements.txt
├── ai_log.md
└── README.md
```

---

*Nhóm OverFitting – SEG301 – Tháng 3/2026*  
*Nguyễn Thanh Trà | Phan Đỗ Thanh Tuấn | Châu Thái Nhật Minh*
