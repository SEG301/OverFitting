"""
Vector Search Engine - Milestone 3
==================================
Sử dụng Sentence-Transformers và FAISS để tìm kiếm theo ngữ nghĩa.
"""

import os
import json
import time
import pickle
import numpy as np
import faiss
from typing import List, Tuple, Optional
from sentence_transformers import SentenceTransformer

# Thêm project root vào path để import BM25Searcher nếu cần
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Paths
DEFAULT_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DEFAULT_VECTOR_INDEX_PATH = os.path.join(DEFAULT_DATA_PATH, "index", "vector_faiss.index")
DEFAULT_DOC_IDS_PATH = os.path.join(DEFAULT_DATA_PATH, "index", "vector_doc_ids.pkl")
DEFAULT_JSONL_PATH = os.path.join(DEFAULT_DATA_PATH, "milestone1_fixed.jsonl")

# Model
# MODEL_NAME = "keepitreal/vietnamese-sbert"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2" # Faster and smaller for demo

class VectorSearcher:
    """
    Vector Search Engine dùng FAISS và Sentence-Transformers.
    """
    
    def __init__(self, 
                 model_name: str = MODEL_NAME,
                 index_path: str = DEFAULT_VECTOR_INDEX_PATH,
                 doc_ids_path: str = DEFAULT_DOC_IDS_PATH,
                 jsonl_path: str = DEFAULT_JSONL_PATH):
        self.model_name = model_name
        self.index_path = index_path
        self.doc_ids_path = doc_ids_path
        self.jsonl_path = jsonl_path
        
        self.model = None
        self.index = None
        self.doc_ids = None # Map FAISS index to doc_id
        
        self._loaded = False
        
    def load_model(self):
        if self.model is None:
            print(f"Loading embedding model: {self.model_name}...")
            start_time = time.time()
            self.model = SentenceTransformer(self.model_name, device="cuda")
            print(f"Model loaded in {time.time() - start_time:.2f}s")
            
    def load_index(self):
        if not os.path.exists(self.index_path) or not os.path.exists(self.doc_ids_path):
            print(f"Vector index not found at {self.index_path}. Please run indexing first.")
            self._loaded = False
            return False
        
        print("Loading FAISS index...")
        self.index = faiss.read_index(self.index_path)
        
        with open(self.doc_ids_path, "rb") as f:
            self.doc_ids = pickle.load(f)
            
        print(f"Loaded FAISS index with {self.index.ntotal} vectors.")
        self._loaded = True
        return True

    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Tìm kiếm top-k dùng vector similarity.
        Trả về: List[(doc_id, score)]
        """
        if not self._loaded:
            if not self.load_index():
                return []
        
        self.load_model()
        
        # Encode query
        query_vector = self.model.encode([query])
        faiss.normalize_L2(query_vector) # Dùng Inner Product (Cosine similarity sau khi normalize)
        
        # Search FAISS
        distances, indices = self.index.search(query_vector, top_k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1:
                doc_id = self.doc_ids[idx]
                results.append((doc_id, float(dist)))
                
        return results

def create_vector_index(jsonl_path: str, output_index_path: str, output_doc_ids_path: str, max_docs: Optional[int] = None):
    """
    Tạo FAISS index từ file JSONL.
    Chỉ nên index text quan trọng: company_name + industries_str_seg.
    """
    model = SentenceTransformer(MODEL_NAME, device="cuda")
    dimension = model.get_sentence_embedding_dimension()
    index = faiss.IndexFlatIP(dimension) # Inner Product on normalized vectors = Cosine Similarity
    
    doc_ids = []
    texts = []
    CHUNK_SIZE = 50000
    count = 0
    total_encoded = 0
    
    print(f"Reading data from {jsonl_path}...")
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if max_docs is not None and count >= max_docs:
                break
            try:
                doc = json.loads(line)
                name = doc.get("company_name", "") or ""
                industry = doc.get("industries_str_seg", "") or doc.get("industries_str", "") or ""
                address = doc.get("address", "") or ""
                rep = doc.get("representative", "") or ""
                status = doc.get("status", "") or ""
                
                text_parts = []
                if name: text_parts.append(f"Tên công ty: {name}.")
                if industry: text_parts.append(f"Ngành nghề kinh doanh: {industry.replace('_', ' ')}.")
                if address: text_parts.append(f"Địa chỉ: {address}.")
                if rep: text_parts.append(f"Người đại diện: {rep}.")
                if status: text_parts.append(f"Trạng thái hoạt động: {status}.")
                
                text = " ".join(text_parts).strip()
                if not text:
                    text = "Không có thông tin doanh nghiệp."
                
                texts.append(text)
                doc_ids.append(i) # Giả sử doc_id là line number
                count += 1
                
                if count % 10000 == 0:
                    print(f"Read {count} documents...")
                
                if len(texts) >= CHUNK_SIZE:
                    print(f"Encoding chunk of {len(texts)} documents (Total read: {count})...")
                    embeddings = model.encode(texts, batch_size=128, show_progress_bar=True)
                    embeddings = np.array(embeddings).astype('float32')
                    faiss.normalize_L2(embeddings)
                    index.add(embeddings)
                    total_encoded += len(texts)
                    texts = []
                    # Free up memory
                    import gc
                    gc.collect()
                    
            except Exception as e:
                print(f"Error parsing line {i}: {e}")
                continue
                
    if len(texts) > 0:
        print(f"Encoding final chunk of {len(texts)} documents...")
        embeddings = model.encode(texts, batch_size=128, show_progress_bar=True)
        embeddings = np.array(embeddings).astype('float32')
        faiss.normalize_L2(embeddings)
        index.add(embeddings)
        total_encoded += len(texts)
        texts = []
        import gc
        gc.collect()
    
    print(f"Processed and indexed {total_encoded} documents in total.")
    print(f"Saving FAISS index to {output_index_path}...")
    faiss.write_index(index, output_index_path)
    
    with open(output_doc_ids_path, "wb") as f:
        pickle.dump(doc_ids, f)
        
    print("Done!")

if __name__ == "__main__":
    # Test indexing
    os.makedirs(os.path.join(DEFAULT_DATA_PATH, "index"), exist_ok=True)
    
    # Do 1.8 triệu docs thì rất lâu, ở đây demo 100k docs trước cho Milestone 3.
    # Trong môi trường server thật có GPU sẽ nhanh hơn.
    create_vector_index(DEFAULT_JSONL_PATH, DEFAULT_VECTOR_INDEX_PATH, DEFAULT_DOC_IDS_PATH, max_docs=None)
    
    # Test search
    searcher = VectorSearcher()
    results = searcher.search("máy tính chơi game", top_k=5)
    print("Top 5 results for 'máy tính chơi game':")
    for doc_id, score in results:
        print(f"Doc ID: {doc_id}, Score: {score:.4f}")
