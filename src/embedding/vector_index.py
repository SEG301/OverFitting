import os
import json
import numpy as np
import faiss
from typing import List, Tuple, Dict, Any

class VectorSearchIndex:
    """
    A FAISS-based vector search index for efficient similarity search.
    Implements Cosine Similarity via exact inner product (IndexFlatIP) on normalized vectors.
    """
    def __init__(self, dimension: int = 768):
        self.dimension = dimension
        # Since vectors are L2-normalized, Inner Product (IP) is equivalent to Cosine Similarity.
        self.index = faiss.IndexFlatIP(dimension)
        self.index_to_doc_id = {}
        
    def build_index(self, embeddings_file: str, mapping_file: str, chunk_size: int = 100000) -> None:
        """
        Builds the FAISS index iteratively from the binary embeddings file to save memory.
        
        Args:
            embeddings_file: Path to the binary (.bin) numpy file containing float32 vectors.
            mapping_file: Path to the doc_id to index JSON mapping file.
            chunk_size: Number of vectors to load and add to FAISS at a time.
        """
        print(f"Loading document mapping from: {mapping_file}")
        with open(mapping_file, 'r', encoding='utf-8') as f:
            doc_id_to_index = json.load(f)
            
        # Create a reverse mapping: internal numerical index -> Document ID
        self.index_to_doc_id = {v: k for k, v in doc_id_to_index.items()}
        total_vectors = len(self.index_to_doc_id)
        
        print(f"Total documents to index: {total_vectors}")
        
        # Iteratively load vectors to prevent massive RAM spikes
        print(f"Building FAISS Index (FlatIP) chunk by chunk...")
        
        # Get file size to ensure correct reading
        file_size = os.path.getsize(embeddings_file)
        vector_size = self.dimension * 4  # 4 bytes per float32
        expected_vectors = file_size // vector_size
        
        if expected_vectors != total_vectors:
            print(f"Warning: Mapping has {total_vectors} entries but binary file has {expected_vectors} vectors.")
            
        with open(embeddings_file, 'rb') as f:
            vectors_processed = 0
            while vectors_processed < expected_vectors:
                # Read a chunk of bytes
                bytes_to_read = chunk_size * vector_size
                chunk_bytes = f.read(bytes_to_read)
                
                if not chunk_bytes:
                    break
                    
                # Convert bytes to numpy float32 matrix
                chunk_vectors = np.frombuffer(chunk_bytes, dtype=np.float32).reshape(-1, self.dimension)
                
                # Normalize just to be absolutely sure, though pipeline already did it.
                faiss.normalize_L2(chunk_vectors)
                
                # Add to FAISS index
                self.index.add(chunk_vectors)
                
                vectors_processed += chunk_vectors.shape[0]
                print(f"Indexed {vectors_processed}/{expected_vectors} vectors...")
                
        print("Index build completed successfully!")

    def save_index(self, index_path: str, meta_path: str) -> None:
        """
        Saves the FAISS index and the reverse mapping to disk.
        """
        os.makedirs(os.path.dirname(index_path) or ".", exist_ok=True)
        os.makedirs(os.path.dirname(meta_path) or ".", exist_ok=True)
        
        print(f"Saving FAISS index to {index_path}...")
        faiss.write_index(self.index, index_path)
        
        print(f"Saving mapping metadata to {meta_path}...")
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(self.index_to_doc_id, f, ensure_ascii=False)
            
        print("Save completed!")

    def load_index(self, index_path: str, meta_path: str) -> None:
        """
        Loads the FAISS index and the reverse mapping from disk.
        """
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"FAISS index file not found: {index_path}")
        if not os.path.exists(meta_path):
            raise FileNotFoundError(f"Metadata file not found: {meta_path}")
            
        print(f"Loading FAISS index from {index_path}...")
        self.index = faiss.read_index(index_path)
        self.dimension = self.index.d
        
        print(f"Loading metadata from {meta_path}...")
        with open(meta_path, 'r', encoding='utf-8') as f:
            # json keys are always strings, need to convert them back to integers
            loaded_map = json.load(f)
            self.index_to_doc_id = {int(k): v for k, v in loaded_map.items()}
            
        print(f"Loaded {self.index.ntotal} vectors into the index.")

    def search(self, query_vector: np.ndarray, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Searches the FAISS index for the most similar vectors to the query.
        
        Args:
            query_vector: A 1D or 2D numpy array representing the query embedding.
            top_k: Number of top results to retrieve.
            
        Returns:
            A list of dictionaries containing 'doc_id' and 'score' (Cosine Similarity score).
        """
        if self.index.ntotal == 0:
            return []
            
        # Ensure correct shape (batch_size, dimension)
        if len(query_vector.shape) == 1:
            query_vector = query_vector.reshape(1, -1)
            
        if query_vector.shape[1] != self.dimension:
            raise ValueError(f"Query vector dimension must be {self.dimension}")
            
        # We must normalize the query vector for Cosine Similarity
        query_vector = query_vector.astype(np.float32).copy()
        faiss.normalize_L2(query_vector)
        
        # Perform Exact Inner Product search 
        scores, inner_indices = self.index.search(query_vector, top_k)
        
        results = []
        for i in range(top_k):
            idx = int(inner_indices[0][i])
            # If faiss returns -1, it means there are fewer vectors in the index than top_k
            if idx == -1:
                continue
                
            doc_id = self.index_to_doc_id.get(idx)
            score = float(scores[0][i])
            results.append({
                "doc_id": doc_id,
                "score": score
            })
            
        return results

if __name__ == "__main__":
    # Test pipeline with the test sample generated in step 1
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    emb_file = os.path.join(PROJECT_ROOT, "data_sample", "test_out", "test_embeddings.bin")
    map_file = os.path.join(PROJECT_ROOT, "data_sample", "test_out", "test_mapping.json")
    
    idx_out_file = os.path.join(PROJECT_ROOT, "data_sample", "test_out", "faiss.index")
    meta_out_file = os.path.join(PROJECT_ROOT, "data_sample", "test_out", "faiss_meta.json")
    
    search_app = VectorSearchIndex(dimension=768)
    
    if os.path.exists(emb_file) and os.path.exists(map_file):
        # 1. Build Index
        print("\n--- Testing FAISS Build ---")
        search_app.build_index(emb_file, map_file, chunk_size=50) # Small chunk for testing
        
        # 2. Save Index
        print("\n--- Testing FAISS Save ---")
        search_app.save_index(idx_out_file, meta_out_file)
        
        # 3. Load Index instance
        print("\n--- Testing FAISS Load ---")
        new_search_app = VectorSearchIndex()
        new_search_app.load_index(idx_out_file, meta_out_file)
        
        # 4. Search
        print("\n--- Testing FAISS Search ---")
        dummy_query = np.random.rand(1, 768).astype(np.float32)
        results = new_search_app.search(dummy_query, top_k=3)
        print("Search Results (Dummy Query):", results)
