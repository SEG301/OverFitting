import json
import os
import time
import shutil
import psutil
from collections import defaultdict

class SPIMIIndexer:
    def __init__(self, data_path, output_dir, block_size_limit=200000):
        self.data_path = data_path
        self.output_dir = output_dir
        self.blocks_dir = os.path.join(output_dir, "blocks")
        self.block_size_limit = block_size_limit
        self.dictionary = defaultdict(list) 
        self.doc_lengths = {} 
        self.doc_offsets = {} # doc_id -> byte_offset trong file gốc
        self.current_doc_id = 0
        self.block_count = 0
        
        if os.path.exists(self.blocks_dir):
            shutil.rmtree(self.blocks_dir)
        os.makedirs(self.blocks_dir)
        
    def get_memory_usage(self):
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024

    def tokenize(self, text):
        if not text:
            return []
        return [term.lower() for term in text.split()]

    def write_block_to_disk(self):
        if not self.dictionary:
            return

        block_filename = os.path.join(self.blocks_dir, f"block_{self.block_count}.txt")
        print(f"--> Writing block {self.block_count} to {block_filename} (Terms: {len(self.dictionary)})...")
        
        sorted_terms = sorted(self.dictionary.keys())
        
        with open(block_filename, 'w', encoding='utf-8') as f:
            for term in sorted_terms:
                postings = self.dictionary[term]
                postings_str = " ".join([f"{doc_id}:{tf}" for doc_id, tf in postings])
                f.write(f"{term} {postings_str}\n")
        
        self.dictionary.clear()
        self.block_count += 1
        import gc
        gc.collect()

    def index(self):
        print(f"Starting SPIMI Checkpoint indexing...")
        print(f"Data Source: {self.data_path}")
        start_time = time.time()
        
        processed_docs_in_block = 0
        target_fields = ['company_name_seg', 'address_seg', 'industries_str_seg', 'representative_seg']
        
        with open(self.data_path, 'r', encoding='utf-8') as f:
            while True:
                # Lưu offset trước khi đọc dòng
                offset = f.tell() 
                line = f.readline()
                if not line:
                    break
                
                try:
                    doc = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                doc_id = self.current_doc_id
                
                # Lưu doc_offset
                self.doc_offsets[doc_id] = offset
                
                # FIELD BOOSTING STRATEGY (TUNED):
                # Cân bằng lại: Tên * 2, Địa chỉ * 2
                full_text = ""
                
                if 'company_name_seg' in doc and doc['company_name_seg']:
                    full_text += (str(doc['company_name_seg']) + " ") * 2
                
                if 'address_seg' in doc and doc['address_seg']:
                    full_text += (str(doc['address_seg']) + " ") * 2
                    
                if 'industries_str_seg' in doc and doc['industries_str_seg']:
                    full_text += str(doc['industries_str_seg']) + " "
                    
                if 'representative_seg' in doc and doc['representative_seg']:
                    full_text += str(doc['representative_seg']) + " "
                
                terms = self.tokenize(full_text)
                doc_len = len(terms)
                self.doc_lengths[doc_id] = doc_len
                
                term_counts = defaultdict(int)
                for term in terms:
                    term_counts[term] += 1
                
                for term, count in term_counts.items():
                    self.dictionary[term].append((doc_id, count))
                
                self.current_doc_id += 1
                processed_docs_in_block += 1
                
                if processed_docs_in_block >= self.block_size_limit:
                    self.write_block_to_disk()
                    print(f"Processed {self.current_doc_id} docs. Memory: {self.get_memory_usage():.2f} MB")
                    processed_docs_in_block = 0
                    
        if self.dictionary:
            self.write_block_to_disk()
            
        self.save_metadata()
            
        elapsed = time.time() - start_time
        print(f"\nIndexing finished!")
        print(f"Total Docs: {self.current_doc_id}")
        print(f"Time taken: {elapsed:.2f} seconds")

    def save_metadata(self):
        meta_path = os.path.join(self.output_dir, "doc_metadata.json")
        print(f"Saving metadata to {meta_path}...")
        avg_dl = sum(self.doc_lengths.values()) / len(self.doc_lengths) if self.doc_lengths else 0
        
        metadata = {
            "total_docs": self.current_doc_id,
            "avg_doc_len": avg_dl,
            "doc_lengths": self.doc_lengths,
            "doc_offsets": self.doc_offsets
        }
        
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f)

if __name__ == "__main__":
    DATA_FILE = r"e:\Crwal\OverFitting\data\final_data.jsonl"
    OUTPUT_DIR = r"e:\Crwal\OverFitting\data\index_data"
    
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    indexer = SPIMIIndexer(DATA_FILE, OUTPUT_DIR, block_size_limit=200000)
    indexer.index()
