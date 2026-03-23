import os
import sys
import time

# Ensure imports work from project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(PROJECT_ROOT)

from src.embedding.vector_index import VectorSearchIndex

def build_faiss_only():
    print("="*60)
    print("MILESTONE 3: FAISS INDEX BUILDER (STAGE 2)")
    print("="*60)
    
    index_dir = os.path.join(PROJECT_ROOT, "data", "index")
    embeddings_bin = os.path.join(index_dir, "vector_embeddings.bin")
    mapping_json = os.path.join(index_dir, "doc_vector_mapping.json")
    faiss_index = os.path.join(index_dir, "faiss.index")
    faiss_meta = os.path.join(index_dir, "faiss_meta.json")

    if not os.path.exists(embeddings_bin) or not os.path.exists(mapping_json):
        print("Error: vector_embeddings.bin or doc_vector_mapping.json missing in data/index/")
        return

    # Step 2: Build FAISS Index
    print("\nSTEP 2: BUILDING FAISS INDEX FROM PRE-GENERATED EMBEDDINGS...")
    t1 = time.time()
    indexer = VectorSearchIndex(dimension=768)
    indexer.build_index(embeddings_bin, mapping_json)
    indexer.save_index(faiss_index, faiss_meta)
    print(f"FAISS indexing took {time.time() - t1:.2f} seconds.")

    print("\n" + "="*60)
    print("FAISS BUILD SUCCESSFUL!")
    print(f"Indices saved in: {index_dir}")
    print("="*60)

if __name__ == "__main__":
    build_faiss_only()
