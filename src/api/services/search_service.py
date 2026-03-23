import os
import sys
import logging
from typing import List, Dict, Any

# Ensure project modules are explicitly pathable 
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Core Ranking Logic Components
from src.ranking.hybrid_search import HybridSearcher
from src.ranking.query_processing import QueryProcessor
from src.ranking.reranker import DocumentReRanker
from src.api.services.suggestion_service import SuggestionService

# Setting up basic logging
logger = logging.getLogger("SearchService")
logging.basicConfig(level=logging.INFO)

class SearchService:
    """
    Centralized service orchestration bridging algorithmic ranking and the REST API.
    """
    _instance = None
    
    # Singleton pattern avoids loading giant ML models multiple times in FastAPI workers
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SearchService, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def initialize(self, index_override: str = None):
        if self.initialized:
            return
            
        logger.info("Initializing NLP Query Processor...")
        self.processor = QueryProcessor()
        
        logger.info("Initializing Autocomplete Engine...")
        self.suggester = SuggestionService()
        
        logger.info("Initializing Hybrid Searcher (BM25 + FAISS Vector)...")
        # Define base data directories
        self.data_dir = os.path.join(PROJECT_ROOT, "data") if not index_override else index_override
        if not os.path.exists(os.path.join(self.data_dir, "index", "term_dict.pkl")):
             self.data_dir = os.path.join(PROJECT_ROOT, "data_sample")
             logger.warning(f"Using {self.data_dir} indices because /data/index is missing.")
             
        bm25_idx = os.path.join(self.data_dir, "index")
        
        # Check if vector db exists, else disable semantic search to avoid ID Mismatch
        vector_idx_path = os.path.join(self.data_dir, "index", "faiss.index")
        vector_meta_path = os.path.join(self.data_dir, "index", "faiss_meta.json")
        
        if not os.path.exists(vector_idx_path):
             logger.warning("FAISS vector index missing! Search will use BM25 only (Lexical Search).")
             # We set these to None or specific dummy to allow HybridSearcher to handle it
             vector_idx_path = None
             vector_meta_path = None

        # Load main dataset
        jsonl_path = os.path.join(self.data_dir, "milestone1_fixed.jsonl")    
        
        # We start building Autocomplete in background basically or blocking
        self.suggester.build_from_jsonl(jsonl_path, max_docs=200000) # fast threshold

        self.hybrid = HybridSearcher(
            bm25_index_dir=bm25_idx,
            jsonl_path=jsonl_path,
            faiss_index_path=vector_idx_path,
            faiss_meta_path=vector_meta_path
        )
        
        logger.info("Initializing Cross-Encoder Re-Ranker...")
        # A smaller model ensures API stays < 300ms 
        self.reranker = DocumentReRanker(model_name="amberoad/bert-multilingual-passage-reranking-msmarco", batch_size=32)
        
        self.initialized = True
        logger.info("Search Service fully booted.")

    def search(self, raw_query: str, top_k: int = 10, skip: int = 0, use_reranker: bool = True, filters: dict = None, is_tax_code: bool = False) -> List[Dict[str, Any]]:
        """
        Executes the entire search pipeline with Filters:
        1. NLP Preprocessing
        2. Hybrid (BM25 + Vector) Retrieval (Top 100 docs)
        3. Simple structured Metadata filter
        4. Cross-Encoder Re-ranking (Top 10)
        """
        if filters is None:
            filters = {}
            
        # 1. NLP Clean
        nlp_res = self.processor.process(raw_query)
        processed_query = nlp_res["final_string"]
        logger.info(f"Query parsed: '{raw_query}' -> '{processed_query}'")

        # Special Mode: Exact Tax Code Match (O(1) lookup)
        if is_tax_code:
            tax_id = str(raw_query).strip().replace(".", "").replace(" ", "").replace("-", "")
            uid = self.suggester.tax_to_id.get(tax_id)
            if uid:
                cached_name = self.suggester.id_names.get(uid, "Company " + uid)
                return [{
                    "universal_id": uid,
                    "company_name": cached_name,
                    "description": f"Mã số thuế: {tax_id}",
                    "score": 1.0
                }]
            return [] # No exact match found

        # 2. Parallel Hybrid Execution (Concurrent BM25 & Vector)
        from concurrent.futures import ThreadPoolExecutor
        
        # Performance Tweaking: Use smaller pool for faster response if no filters
        pool_size = min(200, (skip + top_k) * 10) if filters else 40
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            # We run the hybrid search which is already optimized
            hybrid_candidates = self.hybrid.search(
                query=processed_query, 
                top_k=pool_size,
                fusion_strategy="weighted"
            )

        # EARLY EXIT OPTIMIZATION: 
        # If the top candidate is an extremely high confidence match (> 0.95),
        # skip re-ranking to save ~200-500ms.
        if hybrid_candidates and hybrid_candidates[0].get("final_score", 0) > 0.95:
            logger.info("Early-Exit triggered: Top result is highly confident. Skipping Re-ranker.")
            use_reranker = False
        
        # 3. Apply Metadata Structured Filters over candidates
        if filters:
            filtered_candidates = []
            for doc in hybrid_candidates:
                # Use name cache for ultra fast filtering if needed
                uid = str(doc.get("universal_id"))
                meta = doc.get("meta") or {}
                # Ensure we have the latest name from cache
                cached_name = self.suggester.id_names.get(uid)
                if cached_name: meta["company_name"] = cached_name
                
                passed = True
                if filters.get("location") and filters["location"].lower() not in str(meta.get("address", "")).lower():
                    passed = False
                if filters.get("industry") and filters["industry"].lower() not in str(meta.get("industries_str_seg", "")).replace("_"," ").lower():
                    passed = False
                    
                if passed:
                    filtered_candidates.append(doc)
            hybrid_candidates = filtered_candidates
        
        # 4. Neural Re-Ranking (Reduced to Top 12 for speed)
        if use_reranker and hybrid_candidates:
            # We only re-rank the top 12 elite candidates to ensure UI latency stays < 250ms
            final_docs = self.reranker.rerank(processed_query, hybrid_candidates, top_k=min(12, skip + top_k))
        else:
            final_docs = hybrid_candidates
            
        # Apply Pagination Slice
        final_docs = final_docs[skip : skip + top_k]
            
        # Format response
        formatted_results = []
        
        for doc in final_docs:
            uid = str(doc.get("universal_id"))
            
            # INSTANT SUCCESS: Lookup name from In-Memory Cache (0ms)
            cached_name = self.suggester.id_names.get(uid)
            meta = doc.get("meta") or {}
            
            # Format response without any JSONL Disk Seeks
            formatted_results.append({
                "universal_id": uid,
                "company_name": cached_name or meta.get("company_name", "N/A"),
                "description": meta.get("description") or meta.get("industries_str_seg", "").replace("_"," "),
                "score": doc.get("cross_score", doc.get("final_score", 0.0))
            })
            
        return formatted_results

    def get_company(self, universal_id: str) -> Dict[str, Any]:
        """
        Directly looks up a company by its ID (mostly URL or Tax Code) 
        using a fast O(V) NVMe string scan (grep) directly avoiding RAM overload.
        """
        import subprocess
        import json
        import urllib.parse
        
        try:
            # Decode any residual URL encoding from Next.js path/axios transport
            universal_id = urllib.parse.unquote(urllib.parse.unquote(universal_id))
            
            # O(1) lookup using offset map from SuggestionService
            offset = self.suggester.id_offsets.get(str(universal_id))
            if offset is not None:
                jsonl_file = getattr(self.hybrid.bm25, "jsonl_file", None)
                if jsonl_file is not None:
                    jsonl_file.seek(offset)
                    line_data = jsonl_file.readline().decode('utf-8', errors='ignore')
                    doc = json.loads(line_data)
                    
                    # Formatting matching UI expectations
                    doc["universal_id"] = universal_id
                    doc["id"] = doc.get("tax_code", universal_id)
                    
                    if "industries_arr_seg" in doc and "tags" not in doc:
                        doc["tags"] = doc["industries_arr_seg"]
                    
                    # Enhanced Description Fallback
                    if not doc.get("description"):
                        if doc.get("industries_str_seg"):
                            doc["description"] = f"Doanh nghiệp đăng ký hoạt động trong các lĩnh vực: {doc['industries_str_seg'].replace('_', ' ')}"
                        elif doc.get("industries_detail"):
                            # Handle list of dicts or list of strings
                            details = doc.get("industries_detail")
                            if isinstance(details, list) and len(details) > 0:
                                if isinstance(details[0], dict):
                                    industry_names = [d.get("name") for d in details if d.get("name")]
                                    doc["description"] = f"Lĩnh vực hoạt động chính: {', '.join(industry_names)}"
                                else:
                                    doc["description"] = f"Lĩnh vực hoạt động: {', '.join(details)}"
                        else:
                            doc["description"] = f"Thông tin chi tiết về doanh nghiệp {doc.get('company_name')} đang được cập nhật."
                        
                    return doc
            else:
                return {
                    "id": universal_id,
                    "company_name": "Không có thông tin chi tiết",
                    "message": "Không tìm thấy dữ liệu trong Database (Offset Null)"
                }
        except Exception as e:
            logger.error(f"Error fetching company details via offset fast lookup: {e}")
            
        return {
            "id": universal_id,
            "company_name": "Không có thông tin chi tiết",
            "message": "Không thể trích xuất Database"
        }
