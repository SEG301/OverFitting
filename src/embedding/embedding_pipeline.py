import json
import os
import re
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from typing import Iterator, Tuple, List

def preprocess_text(text: str) -> str:
    """
    Normalizes text by lowercasing, stripping whitespace, and removing extra spaces.
    """
    if not text:
        return ""
    text = str(text).lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text

def extract_and_combine_fields(doc: dict) -> str:
    """
    Extract relevant fields and format them as one combined entry.
    Fields used: company_name + description + reviews + tags.
    """
    parts = []
    
    for field in ['company_name', 'description', 'reviews', 'tags']:
        val = doc.get(field, "")
        if isinstance(val, list):
            # Complex/nested list structures (e.g., list of dictionary reviews)
            if len(val) > 0 and isinstance(val[0], dict):
                # Flatten dictionary values
                val = " ".join(str(v) for item in val for k, v in item.items() if v)
            else:
                # Flat list of items
                val = " ".join(str(item) for item in val if item)
        
        if val:
            parts.append(preprocess_text(str(val)))
            
    combined_text = " ".join(parts)
    # The 'intfloat/multilingual-e5-base' model works best with "passage: " prefix for document embeddings 
    return f"passage: {combined_text}"

def load_data(file_path: str, batch_size: int = 64) -> Iterator[Tuple[List[str], List[str]]]:
    """
    Loads data lazily in batches from the large JSONL dataset to optimize memory.
    Yields: Lists of document IDs and lists of formatted document texts.
    """
    doc_ids = []
    texts = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
                # Ensure the 'id' field is present using fallback keys
                doc_id = doc.get('id') or doc.get('doc_id') or doc.get('url')
                if not doc_id:
                    continue
                    
                combined_text = extract_and_combine_fields(doc)
                doc_ids.append(str(doc_id))
                texts.append(combined_text)
                
                if len(texts) >= batch_size:
                    yield doc_ids, texts
                    doc_ids = []
                    texts = []
            except json.JSONDecodeError:
                continue
    
    # Yield any remaining documents after the loop concludes
    if texts:
        yield doc_ids, texts

def generate_embeddings(model: SentenceTransformer, texts: List[str]) -> np.ndarray:
    """
    Generates semantic vectors for a batch of input text.
    """
    # L2 normalization helps make Cosine Similarity equivalent to native Dot Product in Faiss.
    embeddings = model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
    return embeddings

def save_embeddings(
    input_file: str, 
    embeddings_file: str, 
    mapping_file: str, 
    model_name: str = "intfloat/multilingual-e5-base", 
    batch_size: int = 64, 
    device: str = None
):
    """
    Pipeline orchestrator: 
    1. Inits the model
    2. Loads documents incrementally
    3. Triggers embeddings generation
    4. Writes native binary embeddings to disk efficiently
    """
    if device is None:
        import torch
        if torch.backends.mps.is_available():
            # Great option for Apple Silicon Mac optimizations
            device = "mps"
        elif torch.cuda.is_available():
            device = "cuda"
        else:
            device = "cpu"
            
    print(f"[{device.upper()}] Loading Model '{model_name}'...")
    model = SentenceTransformer(model_name, device=device)
    
    print("Pre-calculating total documents to align progress tracking...")
    # Extremely fast counting of large files in standard pure-python
    total_lines = sum(1 for _ in open(input_file, 'rb'))
    
    doc_id_to_index = {}
    current_index = 0
    
    # Make sure output directories exist
    os.makedirs(os.path.dirname(embeddings_file) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(mapping_file) or ".", exist_ok=True)
    
    print(f"Executing... Embeddings will be iteratively written to: {embeddings_file}")
    with open(embeddings_file, 'wb') as f_emb:
        
        data_generator = load_data(input_file, batch_size=batch_size)
        
        with tqdm(total=total_lines, desc="Encoding Progress") as pbar:
            for doc_ids, texts in data_generator:
                batch_len = len(texts)
                
                # Fetch generated embeddings batch
                embeddings = generate_embeddings(model, texts)
                
                # Directly write highly-compatible raw float32 binary format
                # Extremely memory-efficient, unrollable via np.fromfile or directly loadable in faiss
                f_emb.write(embeddings.astype(np.float32).tobytes())
                
                # Append sequential indexes to doc lookup mapping
                for d_id in doc_ids:
                    doc_id_to_index[d_id] = current_index
                    current_index += 1
                    
                pbar.update(batch_len)
                
    print(f"\nConstructing ID-To-Vector metadata in {mapping_file}...")
    with open(mapping_file, 'w', encoding='utf-8') as f_map:
        json.dump(doc_id_to_index, f_map, ensure_ascii=False)
        
    print(f"\n🚀 Pipeline Completed! Handled {current_index} individual documents.")
    emb_dim = model.get_sentence_embedding_dimension()
    print("-" * 65)
    print(f"Load the compiled binary into numpy or faiss structure via:")
    print(f" >>> embeddings = np.fromfile('{embeddings_file}', dtype=np.float32).reshape({current_index}, {emb_dim})")
    print("-" * 65)

if __name__ == "__main__":
    # Resolve roots dynamically from the location of this pipeline script
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    # Using specific milestone fallback paths
    INPUT_DATA = os.path.join(PROJECT_ROOT, "data_sample", "milestone1_fixed.jsonl")
    if not os.path.exists(INPUT_DATA):
        INPUT_DATA = os.path.join(PROJECT_ROOT, "data", "milestone1_fixed.jsonl")
        
    OUTPUT_EMBEDDINGS = os.path.join(PROJECT_ROOT, "data", "index", "vector_embeddings.bin")
    OUTPUT_MAPPING = os.path.join(PROJECT_ROOT, "data", "index", "doc_vector_mapping.json")

    save_embeddings(
        input_file=INPUT_DATA,
        embeddings_file=OUTPUT_EMBEDDINGS,
        mapping_file=OUTPUT_MAPPING,
        batch_size=64  # Modify batch size corresponding to max GPU/MPS memory availability
    )
