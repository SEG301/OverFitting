"""
FastAPI Server - Milestone 3
================================
Backend API cho giao diện tìm kiếm doanh nghiệp.
Sử dụng FastAPI + Uvicorn cho hiệu năng cao.
"""

import os
import sys
import time

# Thêm project root vào path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from src.ranking.bm25 import BM25Searcher
from src.ranking.vector import VectorSearcher

# ============================================================================
# INIT APP
# ============================================================================

app = FastAPI(title="OverFitting Search Engine", version="3.0")

# Static files
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ============================================================================
# GLOBAL SEARCHERS
# ============================================================================

INDEX_DIR = os.path.join(PROJECT_ROOT, "data", "index")
JSONL_PATH = os.path.join(PROJECT_ROOT, "data", "milestone1_fixed.jsonl")

print("=" * 60)
print("  🔍 OverFitting Search Engine — FastAPI")
print("=" * 60)

bm25_searcher = BM25Searcher(index_dir=INDEX_DIR, jsonl_path=JSONL_PATH)
bm25_searcher.load_index()

vector_searcher = VectorSearcher(jsonl_path=JSONL_PATH)
vector_loaded = vector_searcher.load_index()
if vector_loaded:
    vector_searcher.load_model()

print("=" * 60)
print("  ✅ All systems ready!")
print("=" * 60)

# Load MST index
import pickle
mst_index_path = os.path.join(INDEX_DIR, "mst_index.pkl")
mst_index = {}
if os.path.exists(mst_index_path):
    print("Loading MST Index for O(1) lookup...")
    with open(mst_index_path, "rb") as f:
        mst_index = pickle.load(f)
    print(f"Loaded MST Index: {len(mst_index):,} records")
else:
    print("⚠️ No mst_index.pkl found (Searching by MST will be O(N)!)")


# ============================================================================
# HELPERS
# ============================================================================

def _meta_to_dict(meta: dict) -> dict:
    return {
        "company_name": meta.get("company_name", ""),
        "tax_code": meta.get("tax_code", ""),
        "address": meta.get("address", ""),
        "representative": meta.get("representative", ""),
        "status": meta.get("status", ""),
        "industry": (meta.get("industries_str_seg", "") or "").replace("_", " "),
    }


def hybrid_search(query: str, top_k: int = 10, alpha: float = 0.65):
    pool = max(top_k * 3, 50)
    bm25_results = bm25_searcher.search(query, top_k=pool)
    vector_results = vector_searcher.search(query, top_k=pool) if vector_loaded else []

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


# ============================================================================
# ROUTES
# ============================================================================

@app.get("/")
async def index():
    return FileResponse(os.path.join(TEMPLATES_DIR, "index.html"))


@app.get("/api/search")
async def api_search(
    q: str = Query("", description="Search query"),
    mode: str = Query("hybrid", description="bm25 | vector | hybrid"),
    top_k: int = Query(10, ge=1, le=2000),
    alpha: float = Query(0.65, ge=0.0, le=1.0),
):
    if not q.strip():
        return {"error": "Empty query", "results": [], "time_ms": 0}

    import re
    import json
    # 1. Nhận diện định danh (MST) để quét nguyên thuỷ
    q_clean = q.strip()
    is_id = bool(re.match(r"^[\d\-\.\s]{8,15}$", q_clean))
        
    start = time.time()

    if is_id:
        found_docs = []
        try:
            if mst_index:
                # O(1) Lookup with Hash Map
                if q_clean in mst_index:
                    byte_offset = mst_index[q_clean]
                    # We can use the already opened jsonl file via BM25Searcher
                    if bm25_searcher.jsonl_file:
                        bm25_searcher.jsonl_file.seek(byte_offset)
                        raw_line = bm25_searcher.jsonl_file.readline()
                        line = raw_line.decode("utf-8", errors="ignore")
                        doc = json.loads(line)
                        found_docs.append({
                            "doc_id": -1,
                            "score": 100.0,
                            **_meta_to_dict(doc)
                        })
            else:
                # Fallback to O(N) linear scan if index is missing
                q_mst = f'"tax_code": "{q_clean}"'
                with open(bm25_searcher.jsonl_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if q_mst in line:
                            doc = json.loads(line)
                            found_docs.append({
                                "doc_id": -1,
                                "score": 100.0,
                                **_meta_to_dict(doc)
                            })
                            break
        except Exception:
            pass
            
        if len(found_docs) > 0:
            elapsed = (time.time() - start) * 1000
            return {
                "query": q,
                "mode": "exact_mst",
                "results": found_docs,
                "total": len(found_docs),
                "time_ms": round(elapsed, 1)
            }

    if mode == "bm25":
        raw = bm25_searcher.search(q, top_k=max(top_k * 3, 50))
        results = [
            {"doc_id": doc_id, "score": round(score, 4), **_meta_to_dict(meta)}
            for doc_id, score, meta in raw
        ]
    elif mode == "vector":
        raw = vector_searcher.search(q, top_k=max(top_k * 3, 50)) if vector_loaded else []
        results = []
        for doc_id, score in raw:
            meta = bm25_searcher._get_doc_metadata(doc_id)
            results.append({"doc_id": doc_id, "score": round(score, 4), **_meta_to_dict(meta)})
    else:
        results = hybrid_search(q, top_k=top_k, alpha=alpha)
        
    # 2. Áp dụng Exact Match Boost (Tôn trọng tuyệt đối Tên danh tính & Địa chỉ)
    q_lower = q_clean.lower()
    q_words_list = q_lower.split()
    q_words = len(q_words_list)
    if q_words >= 2:
        q_words_set = set(q_words_list)
        for r in results:
            comp_name = r.get("company_name", "").lower().strip()
            addr = r.get("address", "").lower().strip()
            
            # Ưu tiên theo tên công ty
            if comp_name == q_lower:
                r["score"] += 100.0  # Khớp tuyệt đối tên công ty
            elif f" {q_lower} " in f" {comp_name} ":
                r["score"] += 50.0   # Khớp chính xác cụm từ khóa bên trong tên
            else:
                # Tìm kiếm 1 phần tên doanh nghiệp (cho phép bị xen từ, VD: "Công ty abc" -> "Công ty TNHH abc")
                comp_words_set = set(comp_name.split())
                if q_words_set.issubset(comp_words_set):
                    r["score"] += 30.0
                
            # Ưu tiên theo địa chỉ (rất quan trọng cho user)
            if addr == q_lower:
                r["score"] += 90.0   # Khớp tuyệt đối địa chỉ
            elif f"{q_lower}" in f"{addr}":
                r["score"] += 20.0   # Trích 1 phần địa chỉ (VD: "Đường 210, Ấp 1A")

    # Re-sort in case Exact Matches were boosted
    results = sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]
    
    elapsed = (time.time() - start) * 1000

    true_total = len(results)
    if mode == "vector":
        # Vector search doesn't have a natural 'count', so we simulate it or use the pool
        true_total = len(vector_searcher.search(q, top_k=2000)) if vector_loaded else 0
    elif hasattr(bm25_searcher, 'last_match_count'):
        true_total = bm25_searcher.last_match_count

    return {
        "query": q,
        "mode": mode,
        "results": results,
        "total": true_total,
        "time_ms": round(elapsed, 1),
    }


@app.get("/api/stats")
async def api_stats():
    stats = bm25_searcher.get_stats()
    return {
        "total_documents": stats["total_documents"],
        "vocabulary_size": stats["vocabulary_size"],
        "avg_document_length": round(stats["avg_document_length"], 1),
        "vector_index_loaded": vector_loaded,
    }


# ============================================================================
# ENTRY
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
