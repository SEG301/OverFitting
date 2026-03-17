import os
import sys
import logging
import math
import numpy as np
from typing import List, Dict, Callable

# Ensure project modules are explicitly pathable 
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.api.services.search_service import SearchService

logger = logging.getLogger("SearchEvaluator")
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------------
# METRICS IMPLEMENTATION
# ---------------------------------------------------------

def precision_at_k(retrieved: List[str], relevant: set, k: int = 10) -> float:
    retrieved_k = retrieved[:k]
    hits = len(set(retrieved_k).intersection(relevant))
    return hits / k if k > 0 else 0.0

def recall_at_k(retrieved: List[str], relevant: set, k: int = 10) -> float:
    retrieved_k = retrieved[:k]
    hits = len(set(retrieved_k).intersection(relevant))
    return hits / len(relevant) if len(relevant) > 0 else 0.0

def average_precision(retrieved: List[str], relevant: set) -> float:
    ap = 0.0
    hits = 0
    for i, doc_id in enumerate(retrieved):
        if doc_id in relevant:
            hits += 1
            ap += hits / (i + 1.0)
    return ap / len(relevant) if relevant else 0.0

def ndcg_at_k(retrieved: List[str], relevant: set, k: int = 10) -> float:
    dcg = 0.0
    for i, doc_id in enumerate(retrieved[:k]):
        if doc_id in relevant:
            # Binary relevance assumption (1 or 0)
            dcg += 1.0 / math.log2(i + 2)
            
    idcg = 0.0
    for i in range(min(len(relevant), k)):
        idcg += 1.0 / math.log2(i + 2)
        
    return dcg / idcg if idcg > 0 else 0.0

# ---------------------------------------------------------
# EVALUATOR FRAMEWORK
# ---------------------------------------------------------

class Evaluator:
    def __init__(self, ground_truth: Dict[str, List[str]]):
        """
        ground_truth maps query string to a list of universally relevant doc IDs.
        """
        self.ground_truth = {q: set(rels) for q, rels in ground_truth.items()}

    def run_experiment(self, name: str, search_func: Callable, top_k: int = 10, eval_k: int = 10):
        metrics = {"P@K": [], "Recall@K": [], "MAP": [], "NDCG@K": []}
        
        logger.info(f"Running evaluation for algorithm: '{name}'")
        
        for query, relevant_docs in self.ground_truth.items():
            if not relevant_docs:
                continue
                
            # Perform search fetching enough docs for reasonable AP
            results = search_func(query, top_k=max(top_k, eval_k))
            
            # Map standard objects or strings to IDs
            retrieved_ids = []
            for r in results:
                if isinstance(r, dict) and "universal_id" in r:
                    retrieved_ids.append(str(r["universal_id"]))
                elif hasattr(r, "universal_id"):
                    retrieved_ids.append(str(r.universal_id))
                elif isinstance(r, dict) and "id" in r:
                    retrieved_ids.append(str(r["id"]))
                elif isinstance(r, dict) and "doc_id" in r:
                    retrieved_ids.append(str(r["doc_id"]))
                elif isinstance(r, tuple) or isinstance(r, list):
                    retrieved_ids.append(str(r[0]))
                else:
                    retrieved_ids.append(str(r))
            
            metrics["P@K"].append(precision_at_k(retrieved_ids, relevant_docs, k=eval_k))
            metrics["Recall@K"].append(recall_at_k(retrieved_ids, relevant_docs, k=eval_k))
            metrics["MAP"].append(average_precision(retrieved_ids, relevant_docs))
            metrics["NDCG@K"].append(ndcg_at_k(retrieved_ids, relevant_docs, k=eval_k))
            
        return {
            "Method": name,
            f"Precision@{eval_k}": np.mean(metrics["P@K"]),
            f"Recall@{eval_k}": np.mean(metrics["Recall@K"]),
            "MAP": np.mean(metrics["MAP"]),
            f"NDCG@{eval_k}": np.mean(metrics["NDCG@K"])
        }

def display_report(reports: List[Dict]):
    print("\n" + "="*80)
    print(f"{'SEARCH ENGINE QUALITY EVALUATION REPORT':^80}")
    print("="*80)
    print(f"{'Algorithm':<20} | {'P@10':<12} | {'Recall@10':<12} | {'MAP':<12} | {'NDCG@10':<12}")
    print("-" * 80)
    for r in reports:
        print(f"{r['Method']:<20} | {r['Precision@10']:.4f}       | {r['Recall@10']:.4f}      | {r['MAP']:.4f}      | {r['NDCG@10']:.4f}")
    print("="*80 + "\n")


if __name__ == "__main__":
    # ---------------------------------------------------------
    # EXPERIMENT SETUP
    # ---------------------------------------------------------
    print("Initializing Core Components for Test...")
    service = SearchService()
    service.initialize()
    
    # In a real environment, load standard labeled dataset (e.g. MS-Marco style QRELs).
    # Since we lack explicit user clicks/labels, let's create a synthetic Ground Truth map 
    # to demonstrate the pipeline behavior. Assume these IDs are known to be 'highly relevant'
    # against the queries within our data subsets.
    
    synthetic_ground_truth = {
        "công ty xây dựng hà nội": ["0100109106", "0100105304"], # Known ID mockups
        "ngân hàng thương mại": ["0100112437", "0301152753"],
        "phần mềm erp": ["0101435127", "0313580547", "0301460596"],
        "buôn bán bất động sản": ["0303612665", "0312211116", "0101435127"],
        "xuất nhập khẩu thủy sản nông sản": ["0301150123"]
    }
    
    evaluator = Evaluator(synthetic_ground_truth)
    reports = []
    
    # Helper to clean NLP tokens internally for isolated algorithm pipelines
    def clean_query(q):
        return service.processor.process(q)["final_string"]
    
    # 1. Evaluate BM25 Lexical Baseline
    def run_bm25(query, top_k):
        # We reach directly into HybridSearcher's BM25 indexer
        q = clean_query(query)
        try:
             # Based on hybrid's common attribute standard mapping
             return service.hybrid.bm25.search(q, top_k=top_k)
        except AttributeError:
             return [] # Fallback
             
    reports.append(evaluator.run_experiment("Lexical BM25", run_bm25))
    
    # 2. Evaluate Pure Semantic Dense Vector
    def run_vector(query, top_k):
        q = clean_query(query)
        try:
             # Based on hybrid's mapping
             return service.hybrid.vector.search(q, top_k=top_k)
        except AttributeError:
             return [] # Fallback

    reports.append(evaluator.run_experiment("Dense Semantic", run_vector))
    
    # 3. Evaluate Hybrid Ensembled approach (No Deep AI ReRank)
    def run_hybrid(query, top_k):
        # We disable reranking explicitly to test Fusion Logic vs baseline
        return service.search(raw_query=query, top_k=top_k, use_reranker=False)

    reports.append(evaluator.run_experiment("Hybrid RRF/Weighted", run_hybrid))
    
    # 4. Evaluate Deep NLP Cross-Encoder Hybrid
    def run_rerank(query, top_k):
        # Full stack Enterprise pipeline mode
        return service.search(raw_query=query, top_k=top_k, use_reranker=True)

    reports.append(evaluator.run_experiment("Cross-Encoder Rank", run_rerank))
    
    display_report(reports)
