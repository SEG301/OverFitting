import os
import sys
import numpy as np
import json

# Add src to sys.path so we can import the pipeline
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(PROJECT_ROOT, "src"))

from embedding.embedding_pipeline import save_embeddings

def main():
    print("=== Testing Embedding Pipeline ===")
    
    input_file = os.path.join(PROJECT_ROOT, "data_sample", "sample.jsonl")
    
    # We will output to a test directory
    test_out_dir = os.path.join(PROJECT_ROOT, "data_sample", "test_out")
    os.makedirs(test_out_dir, exist_ok=True)
    
    embeddings_file = os.path.join(test_out_dir, "test_embeddings.bin")
    mapping_file = os.path.join(test_out_dir, "test_mapping.json")
    
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found.")
        return
        
    print(f"1. Running pipeline on {input_file}")
    
    # Run with small batch size
    save_embeddings(
        input_file=input_file,
        embeddings_file=embeddings_file,
        mapping_file=mapping_file,
        batch_size=16 
    )
    
    print("\n2. Verifying outputs")
    # Verify mapping file
    with open(mapping_file, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
        
    num_docs = len(mapping)
    print(f"Total documents successfully processed and mapped: {num_docs}")
    
    # Verify embeddings file
    if num_docs > 0:
        emb_dim = 768 # e5-base produces 768-D embeddings
        print(f"Loading {embeddings_file} into numpy...")
        embeddings = np.fromfile(embeddings_file, dtype=np.float32).reshape(num_docs, emb_dim)
        print(f"Loaded embeddings shape: {embeddings.shape}")
        
        # Check first vector norms
        norms = np.linalg.norm(embeddings[:5], axis=1)
        print(f"Norm of first 5 vectors (should be close to 1.0 due to L2 norm): {norms}")
        
        # Sample doc mapping mapping
        first_doc_id = list(mapping.keys())[0]
        first_doc_index = mapping[first_doc_id]
        print(f"First doc ID: {first_doc_id} -> Index: {first_doc_index}")
        
    print("=== Test Pipeline Completed Successfully! ===")

if __name__ == "__main__":
    main()
