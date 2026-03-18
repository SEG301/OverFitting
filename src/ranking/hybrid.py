"""
Hybrid Search Engine - Milestone 3
==================================
Kết hợp BM25 (Lexical) và Vector Search (Semantic) dùng RRF (Reciprocal Rank Fusion).
"""

import os
import sys
import time
from typing import List, Tuple, Dict

# Thêm project root vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.ranking.bm25 import BM25Searcher
from src.ranking.vector import VectorSearcher

class HybridSearcher:
    """
    Searcher kết hợp BM25 và Vector Search.
    """
    
    def __init__(self, 
                 index_dir: str = None, 
                 jsonl_path: str = None):
        # Mặc định lấy từ bm25 settings
        from src.ranking.bm25 import DEFAULT_INDEX_DIR, DEFAULT_JSONL_PATH
        self.index_dir = index_dir or DEFAULT_INDEX_DIR
        self.jsonl_path = jsonl_path or DEFAULT_JSONL_PATH
        
        self.bm25_searcher = BM25Searcher(index_dir=self.index_dir, jsonl_path=self.jsonl_path)
        self.vector_searcher = VectorSearcher()
        
    def load_indexes(self):
        print("Loading indexes for Hybrid Search...")
        self.bm25_searcher.load_index()
        self.vector_searcher.load_index()
        
    def search(self, query: str, top_k: int = 10, alpha: float = 0.5) -> List[Tuple[int, float, dict]]:
        """
        Tìm kiếm Hybrid.
        query: chuỗi tìm kiếm
        top_k: số lượng kết quả
        alpha: trọng số kết hợp (alpha=1: thuần BM25, alpha=0: thuần Vector)
        
        Sử dụng kết hợp Weighted Score đơn giản (vì RRF cần Rank cho cả 1 triệu docs nếu muốn chính xác).
        Ở đây ta lấy Top 100 từ mỗi phương pháp rồi kết hợp.
        """
        # 1. Lấy kết quả từ BM25 (top 100)
        bm25_results = self.bm25_searcher.search(query, top_k=100)
        
        # 2. Lấy kết quả từ Vector (top 100)
        vector_results = self.vector_searcher.search(query, top_k=100)
        
        # 3. Kết hợp dùng RRF (Reciprocal Rank Fusion)
        # RRF score = sum(1 / (k + rank))
        k = 60
        combined_scores = {} # doc_id -> rrf_score
        
        # BM25 rank
        for rank, (doc_id, score, _) in enumerate(bm25_results, 1):
            combined_scores[doc_id] = combined_scores.get(doc_id, 0) + alpha * (1 / (k + rank))
            
        # Vector rank
        for rank, (doc_id, score) in enumerate(vector_results, 1):
            combined_scores[doc_id] = combined_scores.get(doc_id, 0) + (1 - alpha) * (1 / (k + rank))
            
        # Sort top-k
        sorted_ids = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        top_ids = sorted_ids[:top_k]
        
        # Gắn metadata
        results = []
        for doc_id, score in top_ids:
            metadata = self.bm25_searcher._get_doc_metadata(doc_id)
            results.append((doc_id, score, metadata))
            
        return results

if __name__ == "__main__":
    searcher = HybridSearcher()
    searcher.load_indexes()
    
    query = "máy tính chơi game"
    results = searcher.search(query, top_k=5)
    
    print(f"\nHybrid Results for: '{query}'")
    for i, (doc_id, score, meta) in enumerate(results, 1):
        print(f"{i}. {meta.get('company_name')} (Score: {score:.6f})")
