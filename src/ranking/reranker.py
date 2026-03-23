import time
from typing import List, Dict, Any
import torch

try:
    from sentence_transformers import CrossEncoder
except ImportError:
    CrossEncoder = None

class DocumentReRanker:
    """
    Cross-Encoder based Re-ranking system.
    Takes top-K results from a first-stage retriever (like Hybrid Search)
    and re-scores them for highly accurate final ranking.
    """
    def __init__(self, model_name: str = "amberoad/bert-multilingual-passage-reranking-msmarco", batch_size: int = 32):
        """
        Args:
            model_name: The Cross-Encoder model. We override the base prompt default with a 
                        multilingual MS-Marco model, which is much better suited for Vietnamese 
                        than the English-only 'ms-marco-MiniLM-L-6-v2'. Another great alternative 
                        is 'BAAI/bge-reranker-m3'.
            batch_size: Configurable batch size to avoid OOM for large pools.
        """
        if CrossEncoder is None:
            raise ImportError(
                "sentence-transformers is missing. "
                "Please run: pip install sentence-transformers"
            )

        # Determine device (MPS for Apple Silicon Mac optimizations)
        if torch.backends.mps.is_available():
            self.device = "mps"
        elif torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"
            
        print(f"Loading Cross-Encoder '{model_name}' on {self.device.upper()}...")
        self.model = CrossEncoder(model_name, device=self.device)
        self.batch_size = batch_size
        
    def _construct_document_text(self, doc: Dict[str, Any]) -> str:
        """
        Constructs a concise text representation for reranking.
        Focuses only on company name for maximum speed.
        """
        return doc.get("company_name", "")

    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Re-scores a list of documents against the query using the Cross-Encoder.
        
        Args:
            query: The user's search query text.
            documents: List of dicts from the Hybrid Searcher. 
                       Each must contain at least a 'meta' dictionary with document text details.
            top_k: Number of final results to return.
            
        Returns:
            Ranked list of top_k documents with an updated 'cross_score' field.
        """
        if not documents:
            return []
            
        t0 = time.time()
        
        # 1. Prepare (query, document) pairs for the Cross-Encoder input
        pairs = []
        for doc in documents:
            meta = doc.get("meta", {})
            doc_text = self._construct_document_text(meta)
            
            # Fallback if no text could be constructed
            if not doc_text:
                doc_text = str(doc.get("universal_id", "Unknown Document"))
                
            pairs.append((query, doc_text))
            
        # 2. Predict scores with Cross-Encoder
        # Efficient batching is handled natively by sentence-transformers
        scores = self.model.predict(pairs, batch_size=self.batch_size)
        
        # 3. Attach scores and re-sort documents
        for i, doc in enumerate(documents):
            score_val = scores[i]
            # Some Cross-Encoders return a [N, 2] array (classes: irrelevant vs relevant) instead of scalars
            if hasattr(score_val, '__len__') and len(score_val) > 1:
                # Typically, index 1 is the 'relevant' class probability/logit
                score_val = score_val[1]
                
            doc["cross_score"] = float(score_val)
            
        # Sort descending based on cross_encoder relevance score
        documents.sort(key=lambda x: x["cross_score"], reverse=True)
        final_results = documents[:top_k]
        
        latency = (time.time() - t0) * 1000
        print(f"[ReRanker] Re-scored {len(documents)} docs in {latency:.1f}ms")
        
        return final_results

# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("--- Testing Cross-Encoder Re-Ranking ---")
    
    # We use a lightweight multilingual model for testing purposes
    test_reranker = DocumentReRanker(model_name="amberoad/bert-multilingual-passage-reranking-msmarco")
    
    # Dummy results from Hybrid Search (First-stage retrieval)
    dummy_query = "công nghệ phần mềm"
    
    dummy_hybrid_results = [
        {
            "universal_id": "doc1", 
            "final_score": 0.85, 
            "meta": {"company_name": "Công ty Bất Động Sản Hà Nội"}
        },
        {
            "universal_id": "doc2", 
            "final_score": 0.82, 
            "meta": {"company_name": "Tập Đoàn Công Nghệ Công Ty Cổ Phần FPT", "industries_str_seg": "phần_mềm lập_trình"}
        },
        {
            "universal_id": "doc3", 
            "final_score": 0.81, 
            "meta": {"company_name": "Công Ty Trách Nhiệm Hữu Hạn IT Sài Gòn", "industries_str_seg": "công_nghệ_thông_tin viễn_thông"}
        },
        {
            "universal_id": "doc4", 
            "final_score": 0.70, 
            "meta": {"company_name": "Cửa Hàng Quần Áo Trẻ Em"}
        }
    ]
    
    print("\n[Before Re-Ranking] Base scores from Hybrid:")
    for doc in dummy_hybrid_results:
        print(f" - {doc['meta']['company_name']} (Hybrid: {doc['final_score']})")
        
    reranked_results = test_reranker.rerank(dummy_query, dummy_hybrid_results, top_k=2)
    
    print("\n[After Re-Ranking] Top 2 results:")
    for rank, doc in enumerate(reranked_results, 1):
        print(f" #{rank} -> {doc['meta']['company_name']}")
        print(f"      (Cross Score: {doc['cross_score']:.4f} | Old Hybrid: {doc['final_score']})")
