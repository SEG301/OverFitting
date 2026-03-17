import os
import sys
import time
import json
from typing import List, Dict, Any, Tuple
import numpy as np

# Adjust PYTHONPATH to allow importing project modules
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(os.path.join(PROJECT_ROOT, "src"))

from ranking.bm25 import BM25Searcher, DEFAULT_INDEX_DIR, DEFAULT_JSONL_PATH
from embedding.vector_index import VectorSearchIndex
from sentence_transformers import SentenceTransformer

class EnhancedBM25Searcher(BM25Searcher):
    """
    Extends standard BM25Searcher to return a universal ID (URL/string ID) 
    that matches the Vector Index, ensuring perfect record linkage.
    """
    def _get_doc_metadata(self, doc_id: int) -> dict:
        meta = super()._get_doc_metadata(doc_id)
        if not self.doc_offsets or not self.jsonl_file:
            meta["universal_id"] = str(doc_id)
            return meta
            
        try:
            byte_offset = self.doc_offsets[doc_id]
            self.jsonl_file.seek(byte_offset)
            raw_line = self.jsonl_file.readline()
            doc = json.loads(raw_line.decode("utf-8", errors="ignore"))
            
            # Use same fallback sequence as suggestion_service.py
            unix_id = doc.get('url') or doc.get('tax_code') or doc.get('id') or doc.get('doc_id')
            meta["universal_id"] = str(unix_id)
        except Exception:
            meta["universal_id"] = str(doc_id)
            
        return meta


class HybridSearcher:
    """
    Hybrid Search Engine combining Keyword Lexical Search (BM25) 
    with Semantic Similarity Search (FAISS/E5).
    """
    def __init__(
        self, 
        bm25_index_dir: str, 
        jsonl_path: str,
        faiss_index_path: str,
        faiss_meta_path: str,
        model_name: str = "intfloat/multilingual-e5-base",
        bm25_weight: float = 0.6,
        vector_weight: float = 0.4
    ):
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        
        print("Initializing Hybrid Search Components...")
        start_time = time.time()
        
        # 1. Init BM25
        self.bm25 = EnhancedBM25Searcher(index_dir=bm25_index_dir, jsonl_path=jsonl_path)
        self.bm25.load_index()
        
        # 2. Init FAISS
        self.vector_idx = VectorSearchIndex(dimension=768)
        self.vector_idx.load_index(faiss_index_path, faiss_meta_path)
        
        # 3. Init SentenceTransformer (Query encoder)
        device = "mps" if __import__('torch').backends.mps.is_available() else ("cuda" if __import__('torch').cuda.is_available() else "cpu")
        print(f"Loading '{model_name}' on {device.upper()} for online query encoding...")
        self.encoder = SentenceTransformer(model_name, device=device)
        
        print(f"Hybrid Search initialized in {time.time() - start_time:.2f}s")
        
    def _normalize_scores(self, results: List[Dict[str, Any]], score_key: str = "score") -> List[Dict[str, Any]]:
        """Min-Max normalizes scores strictly into a [0, 1] range."""
        if not results:
            return []
            
        scores = [r[score_key] for r in results]
        min_s = min(scores)
        max_s = max(scores)
        
        for r in results:
            if max_s > min_s:
                r["norm_score"] = (r[score_key] - min_s) / (max_s - min_s)
            else:
                r["norm_score"] = 0.5 # fallback when all scores identical
        return results

    def _rrf_score(self, rank: int, k: int = 60) -> float:
        """Calculates Reciprocal Rank Fusion score."""
        return 1.0 / (k + rank)

    def search(self, query: str, top_k: int = 10, fusion_strategy: str = "weighted") -> List[Dict[str, Any]]:
        """
        Executes a combined search query.
        
        Args:
            query: The search literal text.
            top_k: Top results to return strictly.
            fusion_strategy: Either 'weighted' or 'rrf'.
        """
        t0 = time.time()
        pool_size = max(100, top_k * 2) # Fetch enough candidates
        
        # --- 1. BM25 Search ---
        raw_bm25_results = self.bm25.search(query, top_k=pool_size)
        bm25_results = []
        # Suppress BM25 prints, capture data
        for rank, (internal_id, score, meta) in enumerate(raw_bm25_results, 1):
            bm25_results.append({
                "universal_id": meta.get("universal_id"),
                "score": score,
                "rank": rank,
                "meta": meta
            })
            
        # --- 2. Vector Search ---
        query_text = f"query: {query}" # e5-base instruction
        q_emb = self.encoder.encode([query_text], convert_to_numpy=True, normalize_embeddings=True)
        raw_vector_results = self.vector_idx.search(q_emb, top_k=pool_size)
        
        vector_results = []
        for rank, res in enumerate(raw_vector_results, 1):
            vector_results.append({
                "universal_id": res["doc_id"],
                "score": res["score"],
                "rank": rank
            })
            
        # --- 3. Normalize & Link records ---
        self._normalize_scores(bm25_results)    # adds "norm_score"
        self._normalize_scores(vector_results)  # adds "norm_score"
        
        # Build unified mapping using universal_id as key
        combined_map = {}
        
        # Add BM25 docs into map
        for res in bm25_results:
            uid = res["universal_id"]
            combined_map[uid] = {
                "universal_id": uid,
                "bm25_score": res["norm_score"],
                "bm25_rank": res["rank"],
                "vector_score": 0.0,
                "vector_rank": pool_size + 1,  # If not in vector pool, penalize rank
                "meta": res["meta"]
            }
            
        # Add or Merge Vector docs into map
        for res in vector_results:
            uid = res["universal_id"]
            if uid in combined_map:
                combined_map[uid]["vector_score"] = res["norm_score"]
                combined_map[uid]["vector_rank"] = res["rank"]
            else:
                combined_map[uid] = {
                    "universal_id": uid,
                    "bm25_score": 0.0,
                    "bm25_rank": pool_size + 1,
                    "vector_score": res["norm_score"],
                    "vector_rank": res["rank"],
                    "meta": None # Will lazy-load if selected
                }
                
        # --- 4. Fusion Scoring calculation ---
        final_list = list(combined_map.values())
        
        for item in final_list:
            if fusion_strategy == "weighted":
                final_score = (self.bm25_weight * item["bm25_score"]) + (self.vector_weight * item["vector_score"])
                item["final_score"] = final_score
            elif fusion_strategy == "rrf":
                score_rrf = self._rrf_score(item["bm25_rank"]) + self._rrf_score(item["vector_rank"])
                item["final_score"] = score_rrf
            else:
                raise ValueError("fusion_strategy must be 'weighted' or 'rrf'")
                
        # Sort descending by fused score
        final_list.sort(key=lambda x: x["final_score"], reverse=True)
        final_list = final_list[:top_k]
        
        # Lazy-load metadata for vector-only candidates that made it to top_k
        for item in final_list:
            if item["meta"] is None:
                # To get metadata for a vector-only hit, we ideally reverse lookup in BM25 or JSONL
                # For high performance demo, we stub it. In a real db, we'd query by universal_id here.
                item["meta"] = {"company_name": "Fetched from DB...", "universal_id": item["universal_id"]}
                
        latency = (time.time() - t0) * 1000
        print(f"[HybridSearch] Completed in {latency:.1f}ms -> Strategy: {fusion_strategy.upper()}")
        return final_list

if __name__ == "__main__":
    # Test script using generated sample indices
    test_jsonl = os.path.join(PROJECT_ROOT, "data_sample", "sample.jsonl")
    
    # Needs to run on user's actual DB if available, falling back to test indices
    bm25_idx = os.path.join(PROJECT_ROOT, "data", "index")
    if not os.path.exists(os.path.join(bm25_idx, "term_dict.pkl")):
         bm25_idx = os.path.join(PROJECT_ROOT, "data_sample", "index") # Assuming possible sample path
         
    faiss_idx = os.path.join(PROJECT_ROOT, "data_sample", "test_out", "faiss.index")
    faiss_meta = os.path.join(PROJECT_ROOT, "data_sample", "test_out", "faiss_meta.json")
    
    if os.path.exists(faiss_idx):
        try:
            hybrid = HybridSearcher(
                bm25_index_dir=bm25_idx,
                jsonl_path=test_jsonl,
                faiss_index_path=faiss_idx,
                faiss_meta_path=faiss_meta
            )
            
            query = "công nghệ phần mềm hà nội"
            
            # Weighted Test
            print(f"\n--- Testing Combined Output (Weighted, query: '{query}') ---")
            results_w = hybrid.search(query, top_k=3, fusion_strategy="weighted")
            for i, r in enumerate(results_w, 1):
                print(f"#{i} [{r['final_score']:.4f}] {r['meta'].get('company_name', 'N/A')}")
                print(f"   BM25: {r['bm25_score']:.3f} | Vector: {r['vector_score']:.3f}")
                
            # RRF Test
            print(f"\n--- Testing Combined Output (RRF, query: '{query}') ---")
            results_r = hybrid.search(query, top_k=3, fusion_strategy="rrf")
            for i, r in enumerate(results_r, 1):
                print(f"#{i} [{r['final_score']:.4f}] {r['meta'].get('company_name', 'N/A')}")
                print(f"   BM25 Rank: {r['bm25_rank']} | Vector Rank: {r['vector_rank']}")
                
        except Exception as e:
            print(f"Error during Hybrid Test Initialization (Check path configurations): {e}")
    else:
        print("Please ensure Vector indices are generated before testing Hybrid Search.")
