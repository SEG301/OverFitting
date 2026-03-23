import os
import sys
import time

# Ensure imports work from project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(PROJECT_ROOT)

from src.embedding.embedding_pipeline import save_embeddings
from src.embedding.vector_index import VectorSearchIndex

def build_full_milestone3_index():
    print("="*60)
    print("MILESTONE 3: VECTOR INDEX BUILDER")
    print("="*60)
    
    input_data = os.path.join(PROJECT_ROOT, "data", "milestone1_fixed.jsonl")
    if not os.path.exists(input_data):
        print(f"Error: {input_data} not found. Please ensure your data is in data/milestone1_fixed.jsonl")
        return

    index_dir = os.path.join(PROJECT_ROOT, "data", "index")
    os.makedirs(index_dir, exist_ok=True)
    
    embeddings_bin = os.path.join(index_dir, "vector_embeddings.bin")
    mapping_json = os.path.join(index_dir, "doc_vector_mapping.json")
    faiss_index = os.path.join(index_dir, "faiss.index")
    faiss_meta = os.path.join(index_dir, "faiss_meta.json")

    # Step 1: Generate Embeddings
    print("\nSTEP 1: GENERATING EMBEDDINGS (This may take ~1 hour for 1.8M docs)...")
    t0 = time.time()
    save_embeddings(
        input_file=input_data,
        embeddings_file=embeddings_bin,
        mapping_file=mapping_json,
        batch_size=512 # Increase for better MPS performance
    )
    print(f"Embeddings generation took {float(time.time() - t0)/60:.2f} minutes.")

    # Step 2: Build FAISS Index
    print("\nSTEP 2: BUILDING FAISS INDEX...")
    t1 = time.time()
    indexer = VectorSearchIndex(dimension=768)
    indexer.build_index(embeddings_bin, mapping_json)
    indexer.save_index(faiss_index, faiss_meta)
    print(f"FAISS indexing took {time.time() - t1:.2f} seconds.")

    print("\n" + "="*60)
    print("BUILD SUCCESSFUL!")
    print(f"Indices saved in: {index_dir}")
    print("="*60)

if __name__ == "__main__":
    build_full_milestone3_index()
