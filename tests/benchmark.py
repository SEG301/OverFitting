"""
Benchmark & Evaluation Script — Milestone 3
=============================================
Đo lường tốc độ và chất lượng tìm kiếm cho 3 phương pháp:
  - BM25 (Lexical)
  - Vector Search (Semantic - FAISS)
  - Hybrid Search (RRF)

Output: Bảng so sánh tốc độ, Precision@10 heuristic, và chi tiết kết quả.
Tất cả số liệu trong report đều được chứng minh từ script này.
"""

import os
import sys
import json
import time
import re
import io
from collections import defaultdict

# Tee: ghi output ra cả console lẫn file
class TeeWriter:
    def __init__(self, *writers):
        self.writers = writers
    def write(self, text):
        for w in self.writers:
            w.write(text)
            w.flush()
    def flush(self):
        for w in self.writers:
            w.flush()

OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "benchmark_output.txt")
_log_file = open(OUTPUT_FILE, "w", encoding="utf-8")
sys.stdout = TeeWriter(sys.__stdout__, _log_file)

# Thêm project root vào path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.ranking.bm25 import BM25Searcher
from src.ranking.vector import VectorSearcher

# ============================================================================
# CONFIG
# ============================================================================

INDEX_DIR = os.path.join(PROJECT_ROOT, "data", "index")
JSONL_PATH = os.path.join(PROJECT_ROOT, "data", "milestone1_fixed.jsonl")

# 20 queries mẫu với từ khóa kỳ vọng (dùng để tính Precision@10 heuristic)
# Mỗi query kèm danh sách keywords — nếu company_name hoặc industry chứa >= 1 keyword → relevant
TEST_QUERIES = [
    {
        "query": "công ty xây dựng hà nội",
        "keywords": ["xây dựng", "xây_dựng", "kiến trúc", "construction"],
        "type": "Ngành + Địa điểm"
    },
    {
        "query": "phần mềm kế toán",
        "keywords": ["phần mềm", "phần_mềm", "kế toán", "kế_toán", "software"],
        "type": "Sản phẩm chuyên ngành"
    },
    {
        "query": "bất động sản sài gòn",
        "keywords": ["bất động sản", "bất_động_sản", "nhà đất", "real estate"],
        "type": "Ngành + Tên thông dụng"
    },
    {
        "query": "xuất khẩu thủy sản cần thơ",
        "keywords": ["xuất khẩu", "xuất_khẩu", "thủy sản", "thủy_sản", "hải sản"],
        "type": "Ngành + Địa điểm cụ thể"
    },
    {
        "query": "dịch vụ vận tải logistics",
        "keywords": ["vận tải", "vận_tải", "logistics", "chuyển phát", "giao hàng"],
        "type": "Ngành + Từ ngoại lai"
    },
    {
        "query": "sản xuất bao bì",
        "keywords": ["bao bì", "bao_bì", "đóng gói", "sản xuất", "sản_xuất"],
        "type": "Sản xuất"
    },
    {
        "query": "nhà hàng tiệc cưới",
        "keywords": ["nhà hàng", "nhà_hàng", "tiệc cưới", "tiệc_cưới", "ẩm thực", "ẩm_thực"],
        "type": "Dịch vụ"
    },
    {
        "query": "trường học quốc tế",
        "keywords": ["trường học", "trường_học", "giáo dục", "giáo_dục", "quốc tế", "quốc_tế", "education"],
        "type": "Giáo dục"
    },
    {
        "query": "bệnh viện thú y",
        "keywords": ["thú y", "thú_y", "bệnh viện", "bệnh_viện", "chăm sóc", "chăm_sóc", "pet"],
        "type": "Y tế chuyên biệt"
    },
    {
        "query": "shop quần áo thời trang",
        "keywords": ["quần áo", "quần_áo", "thời trang", "thời_trang", "fashion", "may mặc", "may_mặc"],
        "type": "Bán lẻ + Từ lóng"
    },
    {
        "query": "máy tính chơi game",
        "keywords": ["máy tính", "máy_tính", "computer", "game", "gaming", "laptop", "công nghệ", "công_nghệ"],
        "type": "Semantic (AI cần hiểu)"
    },
    {
        "query": "mỹ phẩm làm đẹp",
        "keywords": ["mỹ phẩm", "mỹ_phẩm", "làm đẹp", "làm_đẹp", "cosmetic", "beauty"],
        "type": "Thương mại"
    },
    {
        "query": "tư vấn luật doanh nghiệp",
        "keywords": ["luật", "tư vấn", "tư_vấn", "pháp lý", "pháp_lý", "law", "legal"],
        "type": "Pháp lý"
    },
    {
        "query": "điện máy gia dụng",
        "keywords": ["điện máy", "điện_máy", "gia dụng", "gia_dụng", "điện tử", "điện_tử", "electronic"],
        "type": "Bán lẻ"
    },
    {
        "query": "sửa chữa ô tô",
        "keywords": ["sửa chữa", "sửa_chữa", "ô tô", "ô_tô", "xe hơi", "xe_hơi", "auto"],
        "type": "Dịch vụ"
    },
    {
        "query": "du lịch lữ hành",
        "keywords": ["du lịch", "du_lịch", "lữ hành", "lữ_hành", "travel", "tour"],
        "type": "Du lịch"
    },
    {
        "query": "khách sạn 5 sao",
        "keywords": ["khách sạn", "khách_sạn", "hotel", "resort", "lưu trú", "lưu_trú"],
        "type": "Hospitality + Số"
    },
    {
        "query": "thực phẩm sạch",
        "keywords": ["thực phẩm", "thực_phẩm", "nông sản", "nông_sản", "organic", "sạch", "food"],
        "type": "Nông sản"
    },
    {
        "query": "năng lượng mặt trời",
        "keywords": ["năng lượng", "năng_lượng", "mặt trời", "mặt_trời", "solar", "điện", "energy"],
        "type": "Công nghệ xanh"
    },
    {
        "query": "giải trí truyền thông",
        "keywords": ["giải trí", "giải_trí", "truyền thông", "truyền_thông", "media", "entertainment"],
        "type": "Media"
    },
]


def is_relevant(result, keywords):
    """
    Kiểm tra 1 kết quả có relevant không, dựa trên keyword matching.
    Kiểm tra cả company_name và industry.
    """
    name = (result.get("company_name", "") or "").lower()
    industry = (result.get("industry", "") or result.get("industries_str_seg", "") or "").lower().replace("_", " ")
    text = f"{name} {industry}"
    
    for kw in keywords:
        kw_normalized = kw.lower().replace("_", " ")
        if kw_normalized in text:
            return True
    return False


def precision_at_k(results, keywords, k=10):
    """Tính Precision@K thực tế dựa trên keyword matching."""
    top_k = results[:k]
    if not top_k:
        return 0.0
    relevant = sum(1 for r in top_k if is_relevant(r, keywords))
    return relevant / len(top_k)


def _meta_to_dict(meta):
    return {
        "company_name": meta.get("company_name", ""),
        "tax_code": meta.get("tax_code", ""),
        "address": meta.get("address", ""),
        "representative": meta.get("representative", ""),
        "status": meta.get("status", ""),
        "industry": (meta.get("industries_str_seg", "") or "").replace("_", " "),
    }


def hybrid_search_fn(bm25_searcher, vector_searcher, query, top_k=10, alpha=0.65):
    """Hybrid search (RRF) function — same logic as server.py."""
    bm25_results = bm25_searcher.search(query, top_k=top_k * 2)
    vector_results = vector_searcher.search(query, top_k=top_k * 2)

    k = 60
    combined = {}
    for rank, (doc_id, score, _) in enumerate(bm25_results, 1):
        combined[doc_id] = combined.get(doc_id, 0) + alpha * (1 / (k + rank))
    for rank, (doc_id, score) in enumerate(vector_results, 1):
        combined[doc_id] = combined.get(doc_id, 0) + (1 - alpha) * (1 / (k + rank))

    sorted_ids = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:top_k]
    results = []
    for doc_id, rrf_score in sorted_ids:
        meta = bm25_searcher._get_doc_metadata(doc_id)
        results.append({"doc_id": doc_id, "score": round(rrf_score, 6), **_meta_to_dict(meta)})
    return results


def run_benchmark():
    """Main benchmark: đo tốc độ và Precision@10 cho cả 3 phương pháp."""
    
    print("=" * 80)
    print("  BENCHMARK & EVALUATION — Milestone 3 — OverFitting Search Engine")
    print("=" * 80)
    
    # --- Load searchers ---
    print("\n[1/4] Loading BM25 Searcher...")
    bm25 = BM25Searcher(index_dir=INDEX_DIR, jsonl_path=JSONL_PATH)
    bm25.load_index()
    stats = bm25.get_stats()
    print(f"  Total documents: {stats['total_documents']:,}")
    print(f"  Vocabulary size: {stats['vocabulary_size']:,}")
    print(f"  Avg doc length: {stats['avg_document_length']:.1f} tokens")
    
    print("\n[2/4] Loading Vector Searcher (FAISS)...")
    vec = VectorSearcher(jsonl_path=JSONL_PATH)
    vec_loaded = vec.load_index()
    if vec_loaded:
        vec.load_model()
        # Detect index type
        try:
            nprobe = vec.index.nprobe
            index_type = f"IVFFlat (nprobe={nprobe})"
        except AttributeError:
            index_type = "FlatIP (brute-force)"
        print(f"  FAISS index type: {index_type}")
        print(f"  Total vectors: {vec.index.ntotal:,}")
    else:
        print("  [WARNING] Vector index not found! Skipping Vector & Hybrid tests.")
    
    # --- Warmup ---
    print("\n[3/4] Warmup (1 query each mode)...")
    _ = bm25.search("test warmup", top_k=10)
    if vec_loaded:
        _ = vec.search("test warmup", top_k=10)
    print("  Done.")
    
    # --- Benchmark ---
    print(f"\n[4/4] Running benchmark on {len(TEST_QUERIES)} queries...")
    print()
    
    bm25_times = []
    vec_times = []
    hybrid_times = []
    bm25_precisions = []
    vec_precisions = []
    hybrid_precisions = []
    
    header = f"{'#':<3} {'Query':<35} {'BM25 ms':<10} {'Vec ms':<10} {'Hyb ms':<10} {'P@10 BM25':<10} {'P@10 Vec':<10} {'P@10 Hyb':<10}"
    print(header)
    print("-" * len(header))
    
    for i, tq in enumerate(TEST_QUERIES, 1):
        query = tq["query"]
        keywords = tq["keywords"]
        
        # --- BM25 ---
        t0 = time.perf_counter()
        bm25_raw = bm25.search(query, top_k=10)
        bm25_time = (time.perf_counter() - t0) * 1000
        bm25_results = [{"doc_id": d, "score": s, **_meta_to_dict(m)} for d, s, m in bm25_raw]
        bm25_p10 = precision_at_k(bm25_results, keywords, k=10)
        bm25_times.append(bm25_time)
        bm25_precisions.append(bm25_p10)
        
        # --- Vector ---
        if vec_loaded:
            t0 = time.perf_counter()
            vec_raw = vec.search(query, top_k=10)
            vec_time = (time.perf_counter() - t0) * 1000
            vec_results = []
            for doc_id, score in vec_raw:
                meta = bm25._get_doc_metadata(doc_id)
                vec_results.append({"doc_id": doc_id, "score": score, **_meta_to_dict(meta)})
            vec_p10 = precision_at_k(vec_results, keywords, k=10)
        else:
            vec_time = 0
            vec_p10 = 0
        vec_times.append(vec_time)
        vec_precisions.append(vec_p10)
        
        # --- Hybrid ---
        if vec_loaded:
            t0 = time.perf_counter()
            hybrid_results = hybrid_search_fn(bm25, vec, query, top_k=10, alpha=0.65)
            hybrid_time = (time.perf_counter() - t0) * 1000
            hybrid_p10 = precision_at_k(hybrid_results, keywords, k=10)
        else:
            hybrid_time = 0
            hybrid_p10 = 0
        hybrid_times.append(hybrid_time)
        hybrid_precisions.append(hybrid_p10)
        
        print(f"{i:<3} {query:<35} {bm25_time:<10.1f} {vec_time:<10.1f} {hybrid_time:<10.1f} {bm25_p10:<10.2f} {vec_p10:<10.2f} {hybrid_p10:<10.2f}")
    
    # --- Summary ---
    print()
    print("=" * 80)
    print("  SUMMARY")
    print("=" * 80)
    
    avg_bm25_time = sum(bm25_times) / len(bm25_times)
    avg_vec_time = sum(vec_times) / len(vec_times) if vec_loaded else 0
    avg_hybrid_time = sum(hybrid_times) / len(hybrid_times) if vec_loaded else 0
    
    avg_bm25_p10 = sum(bm25_precisions) / len(bm25_precisions)
    avg_vec_p10 = sum(vec_precisions) / len(vec_precisions) if vec_loaded else 0
    avg_hybrid_p10 = sum(hybrid_precisions) / len(hybrid_precisions) if vec_loaded else 0
    
    print(f"\n  {'Metric':<30} {'BM25':<15} {'Vector':<15} {'Hybrid':<15}")
    print(f"  {'-'*30} {'-'*15} {'-'*15} {'-'*15}")
    print(f"  {'Avg Latency (ms)':<30} {avg_bm25_time:<15.1f} {avg_vec_time:<15.1f} {avg_hybrid_time:<15.1f}")
    print(f"  {'Min Latency (ms)':<30} {min(bm25_times):<15.1f} {min(vec_times):<15.1f} {min(hybrid_times):<15.1f}")
    print(f"  {'Max Latency (ms)':<30} {max(bm25_times):<15.1f} {max(vec_times):<15.1f} {max(hybrid_times):<15.1f}")
    print(f"  {'Avg Precision@10':<30} {avg_bm25_p10:<15.3f} {avg_vec_p10:<15.3f} {avg_hybrid_p10:<15.3f}")
    print(f"  {'Min Precision@10':<30} {min(bm25_precisions):<15.2f} {min(vec_precisions):<15.2f} {min(hybrid_precisions):<15.2f}")
    
    print(f"\n  FAISS Index Type: {index_type if vec_loaded else 'N/A'}")
    print(f"  Total Documents: {stats['total_documents']:,}")
    print(f"  Queries Tested: {len(TEST_QUERIES)}")
    
    # --- Detailed results for 3 sample queries ---
    print("\n" + "=" * 80)
    print("  DETAILED RESULTS (3 sample queries)")
    print("=" * 80)
    
    sample_queries = [0, 10, 18]  # "xây dựng hà nội", "máy tính chơi game", "năng lượng mặt trời"
    
    for idx in sample_queries:
        tq = TEST_QUERIES[idx]
        query = tq["query"]
        keywords = tq["keywords"]
        print(f"\n  Query: \"{query}\" (Type: {tq['type']})")
        print(f"  Keywords: {keywords}")
        
        bm25_raw = bm25.search(query, top_k=5)
        bm25_results = [{"doc_id": d, "score": s, **_meta_to_dict(m)} for d, s, m in bm25_raw]
        
        print(f"\n  BM25 Top 5:")
        for j, r in enumerate(bm25_results, 1):
            rel = "✓" if is_relevant(r, keywords) else "✗"
            print(f"    {j}. [{rel}] {r['company_name'][:60]}")
        
        if vec_loaded:
            vec_raw = vec.search(query, top_k=5)
            print(f"\n  Vector Top 5:")
            for j, (doc_id, score) in enumerate(vec_raw, 1):
                meta = bm25._get_doc_metadata(doc_id)
                r = _meta_to_dict(meta)
                rel = "✓" if is_relevant(r, keywords) else "✗"
                print(f"    {j}. [{rel}] {r['company_name'][:60]}")
            
            hybrid_results = hybrid_search_fn(bm25, vec, query, top_k=5, alpha=0.65)
            print(f"\n  Hybrid Top 5:")
            for j, r in enumerate(hybrid_results, 1):
                rel = "✓" if is_relevant(r, keywords) else "✗"
                print(f"    {j}. [{rel}] {r['company_name'][:60]}")
    
    print("\n" + "=" * 80)
    print("  BENCHMARK COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    run_benchmark()
