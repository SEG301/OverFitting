"""
BM25 (Best Matching 25) Ranking Algorithm - Code tay
=====================================================
Milestone 2 - SEG301: Search Engines & Information Retrieval

BM25 là thuật toán ranking dựa trên xác suất, cải tiến từ TF-IDF.

Công thức BM25:
    score(D, Q) = Σ IDF(qi) * (tf(qi, D) * (k1 + 1)) / (tf(qi, D) + k1 * (1 - b + b * |D| / avgdl))

Trong đó:
    - tf(qi, D): Term frequency của query term qi trong document D
    - IDF(qi): Inverse Document Frequency = log((N - df + 0.5) / (df + 0.5) + 1)
    - N: Tổng số documents
    - df: Số documents chứa term qi
    - |D|: Độ dài document D (số terms)
    - avgdl: Độ dài trung bình của tất cả documents
    - k1: Tham số điều chỉnh term frequency saturation (mặc định: 1.2)
    - b: Tham số điều chỉnh document length normalization (mặc định: 0.75)

Lưu ý: KHÔNG sử dụng bất kỳ thư viện ranking nào có sẵn.
Tất cả logic tính toán TF, IDF, BM25 score đều được code tay.

Kiến trúc tối ưu bộ nhớ:
    - term_dict.pkl:  Dict[str, (df, offset, length)] → ~18MB, load nhanh
    - postings.bin:   Binary file → random access khi search
    - doc_lengths.pkl: Dict[int, int] → ~12MB
    - doc_offsets.pkl: Dict[int, int] → ~25MB, byte offset trong JSONL
    - Metadata đọc on-demand từ file JSONL gốc (không load vào RAM)
"""

import os
import sys
import json
import math
import time
import pickle
from typing import Dict, List, Tuple, Optional
from collections import defaultdict

try:
    from pyvi import ViTokenizer
except ImportError:
    ViTokenizer = None


# ============================================================================
# CONFIGURATION
# ============================================================================

# BM25 Parameters
K1 = 1.2    # Term frequency saturation
B = 0.4     # Document length normalization (reduced to prevent overly boosting short documents)

# Performance: Giới hạn số postings entries xử lý cho mỗi term
# Khi df > MAX_POSTINGS_PER_TERM, chỉ xử lý MAX_POSTINGS_PER_TERM entries đầu tiên
# Trade-off: Mất <2% recall nhưng giảm latency 5-10x cho queries phổ biến
MAX_POSTINGS_PER_TERM = 200_000

# Paths
DEFAULT_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DEFAULT_INDEX_DIR = os.path.join(DEFAULT_DATA_PATH, "index")
DEFAULT_JSONL_PATH = os.path.join(DEFAULT_DATA_PATH, "milestone1_fixed.jsonl")


# ============================================================================
# BM25 SEARCH ENGINE
# ============================================================================

class BM25Searcher:
    """
    BM25 Search Engine - Code tay hoàn toàn.
    
    Sử dụng inverted index từ SPIMI (kiến trúc 2-file) để thực hiện 
    ranked retrieval theo thuật toán BM25.
    
    Kiến trúc tối ưu bộ nhớ:
    - Chỉ load term_dict (~18MB) + doc_lengths (~12MB) + doc_offsets (~25MB)
    - Tổng RAM khi khởi động: ~55MB (thay vì >3GB)
    - Postings: đọc từ disk khi search (random access)
    - Metadata: đọc từ JSONL khi cần hiển thị (random access)
    """
    
    def __init__(self, index_dir: str = DEFAULT_INDEX_DIR, 
                 jsonl_path: str = DEFAULT_JSONL_PATH,
                 k1: float = K1, b: float = B):
        self.index_dir = index_dir
        self.jsonl_path = jsonl_path
        self.k1 = k1
        self.b = b
        
        self.term_dict = None         # term -> (df, offset, length)
        self.postings_file = None     # file handle for postings.bin
        self.doc_lengths = None       # doc_id -> document length
        self.doc_offsets = None       # doc_id -> byte offset in JSONL
        self.jsonl_file = None        # file handle for JSONL
        self.total_docs = 0           # N
        self.avg_doc_length = 0.0     # avgdl
        self.vocab_size = 0
        
        self._loaded = False
    
    def load_index(self):
        """
        Load index files nhẹ vào RAM.
        Tổng ~55MB: term_dict + doc_lengths + doc_offsets.
        """
        print("Loading index files...")
        load_start = time.time()
        
        # 1. Load term dictionary (~18MB)
        dict_path = os.path.join(self.index_dir, "term_dict.pkl")
        if not os.path.exists(dict_path):
            raise FileNotFoundError(
                f"Term dictionary not found: {dict_path}\n"
                f"Run spimi.py and merging.py first!"
            )
        with open(dict_path, "rb") as f:
            self.term_dict = pickle.load(f)
        self.vocab_size = len(self.term_dict)
        print(f"  [OK] Term dictionary: {self.vocab_size:,d} terms")
        
        # 2. Mở postings file handle (không load)
        postings_path = os.path.join(self.index_dir, "postings.bin")
        self.postings_file = open(postings_path, "rb")
        print(f"  [OK] Postings file opened (random access)")
        
        # 3. Load document lengths (~12MB) 
        lengths_path = os.path.join(self.index_dir, "doc_lengths.pkl")
        with open(lengths_path, "rb") as f:
            self.doc_lengths = pickle.load(f)
        self.total_docs = len(self.doc_lengths)
        total_length = sum(self.doc_lengths.values())
        self.avg_doc_length = total_length / self.total_docs if self.total_docs > 0 else 0
        print(f"  [OK] Document lengths: {self.total_docs:,d} docs (avg: {self.avg_doc_length:.1f})")
        
        # 4. Load document offsets (~25MB)
        offsets_path = os.path.join(self.index_dir, "doc_offsets.pkl")
        if os.path.exists(offsets_path):
            with open(offsets_path, "rb") as f:
                self.doc_offsets = pickle.load(f)
            print(f"  [OK] Document offsets loaded (for metadata lookup)")
        else:
            self.doc_offsets = None
            print(f"  ⚠ doc_offsets.pkl not found (no metadata display)")
        
        # 5. Mở JSONL file handle ở binary mode (để byte offset khớp với SPIMI)
        if os.path.exists(self.jsonl_path):
            self.jsonl_file = open(self.jsonl_path, "rb")
            print(f"  [OK] JSONL file opened (metadata on-demand)")
        
        load_time = time.time() - load_start
        print(f"  Load time: {load_time:.1f}s")
        
        self._loaded = True
    
    def _get_postings(self, term: str) -> Optional[List[Tuple[int, int]]]:
        """
        Đọc postings list cho 1 term từ binary file.
        Random file seek O(1).
        """
        if term not in self.term_dict:
            return None
        
        df, offset, length = self.term_dict[term]
        self.postings_file.seek(offset)
        postings_bytes = self.postings_file.read(length)
        return pickle.loads(postings_bytes)
    
    def _get_doc_metadata(self, doc_id: int) -> dict:
        """
        Đọc metadata của 1 document từ file JSONL gốc.
        Sử dụng byte offset để seek trực tiếp (không scan toàn bộ file).
        """
        if not self.doc_offsets or not self.jsonl_file:
            return {}
        
        if doc_id not in self.doc_offsets:
            return {}
        
        try:
            byte_offset = self.doc_offsets[doc_id]
            self.jsonl_file.seek(byte_offset)
            raw_line = self.jsonl_file.readline()
            line = raw_line.decode("utf-8", errors="ignore")
            doc = json.loads(line)
            
            # Ưu tiên lấy industries_str_seg, nếu không có thì lấy industries_str
            industry = doc.get("industries_str_seg") or doc.get("industries_str")
            
            # Nếu vẫn không có, thử lấy từ industries_detail (nếu là list)
            if not industry and "industries_detail" in doc:
                details = doc["industries_detail"]
                if isinstance(details, list):
                    industry = ", ".join([d.get("name", "") for d in details if d.get("name")])
            
            # Làm sạch địa chỉ (xóa dấu phẩy và khoảng trắng thừa ở đầu/cuối)
            raw_address = doc.get("address", "")
            clean_address = raw_address.strip(", ")
            
            # Representative fallback
            rep = doc.get("representative", "")
            if not rep or rep.lower() == "none":
                rep = "Chưa cập nhật"
            
            return {
                "company_name": doc.get("company_name", ""),
                "tax_code": doc.get("tax_code", ""),
                "address": clean_address,
                "representative": rep,
                "status": doc.get("status", ""),
                "industries_str_seg": industry or "",
            }
        except Exception:
            return {}
    
    def compute_idf(self, term: str) -> float:
        """
        Tính IDF (Inverse Document Frequency) cho một term.
        
        Công thức IDF theo BM25 (Robertson-Sparck Jones):
            IDF(t) = log((N - df(t) + 0.5) / (df(t) + 0.5) + 1)
        """
        if term not in self.term_dict:
            return 0.0
        
        df = self.term_dict[term][0]
        N = self.total_docs
        idf = math.log((N - df + 0.5) / (df + 0.5) + 1)
        return idf
    
    def compute_tf_component(self, tf: int, doc_length: int) -> float:
        """
        Tính thành phần TF trong công thức BM25.
        
        Công thức:
            tf_component = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * |D| / avgdl))
        """
        length_norm = 1 - self.b + self.b * (doc_length / self.avg_doc_length)
        tf_component = (tf * (self.k1 + 1)) / (tf + self.k1 * length_norm)
        return tf_component
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float, dict]]:
        """
        Tìm kiếm và xếp hạng documents theo BM25.
        
        Quy trình:
        1. Tokenize query
        2. Với mỗi query term: tính IDF, đọc postings (random access từ disk)
        3. Với mỗi document: tính BM25 score = Σ IDF * TF_component
        4. Trả về top-k documents kèm metadata
        
        Tối ưu: Skip terms quá phổ biến (df > 30% corpus) vì:
        - IDF rất thấp → đóng góp score không đáng kể
        - Postings list cực lớn (hàng triệu entries) → unpickle rất chậm
        """
        if not self._loaded:
            self.load_index()
        
        search_start = time.time()
        
        query_tokens = self._tokenize_query(query)
        if not query_tokens:
            return []
        
        # Ngưỡng df tối đa: term xuất hiện > 80% corpus mới bị bỏ qua (thay vì 30%)
        # Vì các từ như "xây dựng" rất quan trọng nhưng lại phổ biến trong dữ liệu doanh nghiệp.
        max_df = int(self.total_docs * 0.8)
        
        # Precompute constants for the hot loop
        doc_scores = defaultdict(float)
        skipped_terms = []
        k1 = self.k1
        b = self.b
        avgdl = self.avg_doc_length
        k1_plus_1 = k1 + 1
        
        # Coordination Factor: Đếm xem mỗi doc_id chứa bao nhiêu query terms khác nhau
        # để ưu tiên các kết quả khớp NHIỀU từ khoá hơn (tránh việc chỉ khớp 1 từ rồi trồi lên đầu).
        doc_term_matches = defaultdict(int)
        
        for term in query_tokens:
            if term not in self.term_dict:
                continue
            
            df = self.term_dict[term][0]
            
            # Skip terms quá phổ biến (df > 80%)
            if df > max_df and len(query_tokens) > 2:
                skipped_terms.append(f"{term}(df={df:,d})")
                continue
            
            idf = self.compute_idf(term)
            if idf <= 0:
                continue
            
            postings = self._get_postings(term)
            if postings is None:
                continue
            
            # Truncate postings nếu quá lớn (tối ưu tốc độ)
            MAX_MATCHES = 400000
            if len(postings) > MAX_MATCHES:
                postings = postings[:MAX_MATCHES]
            
            if not postings:
                continue
            
            # Hot loop - Optimized: Inlined compute_tf_component
            for doc_id, tf in postings:
                doc_length = self.doc_lengths.get(doc_id, avgdl)
                # BM25 TF component
                length_norm = 1 - b + b * (doc_length / avgdl)
                tf_comp = (tf * k1_plus_1) / (tf + k1 * length_norm)
                
                doc_scores[doc_id] += idf * tf_comp
                doc_term_matches[doc_id] += 1
        
        # Lọc ra danh sách các valid tokens thực sự được đưa vào chấm điểm
        valid_tokens = []
        for t in query_tokens:
            if t not in self.term_dict:
                continue
            df = self.term_dict[t][0]
            if df > max_df and len(query_tokens) > 2:
                continue
            if self.compute_idf(t) > 0:
                valid_tokens.append(t)
        
        num_query_tokens = len(valid_tokens)
        if num_query_tokens > 0:
            for doc_id in doc_scores:
                n_matched = doc_term_matches[doc_id]
                coordination_factor = n_matched / num_query_tokens
                doc_scores[doc_id] *= (coordination_factor ** 1.5)
        
        # Top-k
        sorted_docs = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        top_docs = sorted_docs[:top_k]
        
        # Gắn metadata (đọc on-demand từ JSONL)
        results = []
        for doc_id, score in top_docs:
            metadata = self._get_doc_metadata(doc_id)
            results.append((doc_id, score, metadata))
        
        search_time = time.time() - search_start
        
        print(f"\n  Query: \"{query}\"")
        print(f"  Tokens: {query_tokens}")
        if skipped_terms:
            print(f"  Skipped (too common): {', '.join(skipped_terms)}")
        self.last_match_count = len(doc_scores)
        print(f"  Documents matched: {self.last_match_count:,}")
        print(f"  Search time: {search_time*1000:.1f}ms")
        
        return results
    
    def _tokenize_query(self, query: str) -> List[str]:
        """
        Tokenize query text với cơ chế chống chế độ ngữ cảnh của PyVi.
        PyVi sẽ tokenize "CÔNG NGHỆ VIBETEKS" khác với "công nghệ vibeteks".
        Để tối đa Recall, ta tổng hợp các loại hình token.
        """
        import re
        query_clean = re.sub(r'[^\w\s_]', ' ', query)
        
        if ViTokenizer:
            q_lower = ViTokenizer.tokenize(query_clean.lower())
            q_upper = ViTokenizer.tokenize(query_clean.upper()).lower()
            q_uni = query_clean.lower().replace("_", " ")
        else:
            q_lower = query_clean.lower()
            q_upper = ""
            q_uni = ""
            
        combined = f"{q_lower} {q_upper} {q_uni}"
        tokens = combined.split()
        
        result = []
        for token in set(tokens):
            if len(token) <= 1 and not token.isdigit():
                continue
            if all(c in '.,;:!?()-_/\\|@#$%^&*+=<>{}[]"\'~`' for c in token):
                continue
            result.append(token)
        return result
    
    def get_stats(self) -> dict:
        """Trả về thống kê về index."""
        if not self._loaded:
            self.load_index()
        return {
            "total_documents": self.total_docs,
            "vocabulary_size": self.vocab_size,
            "avg_document_length": self.avg_doc_length,
            "k1": self.k1,
            "b": self.b,
        }
    
    def close(self):
        """Đóng file handles."""
        if self.postings_file:
            self.postings_file.close()
            self.postings_file = None
        if self.jsonl_file:
            self.jsonl_file.close()
            self.jsonl_file = None
    
    def __del__(self):
        self.close()


# ============================================================================
# DISPLAY UTILS
# ============================================================================

def display_results(results: List[Tuple[int, float, dict]], query: str):
    """Hiển thị kết quả tìm kiếm."""
    print("\n" + "=" * 80)
    print(f"  🔍 Search Results for: \"{query}\"")
    print(f"  Found {len(results)} results")
    print("=" * 80)
    
    if not results:
        print("  No results found.")
        return
    
    for rank, (doc_id, score, meta) in enumerate(results, 1):
        print(f"\n  #{rank} [Score: {score:.4f}] (Doc ID: {doc_id})")
        print(f"  ├─ Company:  {meta.get('company_name', 'N/A')}")
        print(f"  ├─ Tax Code: {meta.get('tax_code', 'N/A')}")
        print(f"  ├─ Address:  {meta.get('address', 'N/A')}")
        print(f"  ├─ Rep:      {meta.get('representative', 'N/A')}")
        print(f"  ├─ Status:   {meta.get('status', 'N/A')}")
        industries = meta.get('industries_str_seg', 'N/A')
        # Hiển thị đầy đủ và thay thế dấu gạch dưới bằng khoảng trắng cho dễ đọc
        if industries:
            industries = industries.replace("_", " ")
        print(f"  └─ Industry: {industries}")
    
    print("\n" + "=" * 80)


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    index_dir = os.path.join(data_dir, "index")
    jsonl_path = os.path.join(data_dir, "milestone1_fixed.jsonl")
    
    searcher = BM25Searcher(index_dir=index_dir, jsonl_path=jsonl_path)
    searcher.load_index()
    
    stats = searcher.get_stats()
    print(f"\n📊 Index Statistics:")
    for key, val in stats.items():
        print(f"  {key}: {val:,}" if isinstance(val, int) else f"  {key}: {val}")
    
    test_queries = [
        "công_ty công_nghệ thông_tin",
        "bất_động_sản hà_nội",
        "xuất_khẩu thủy_sản",
    ]
    
    for q in test_queries:
        results = searcher.search(q, top_k=5)
        display_results(results, q)
    
    searcher.close()
