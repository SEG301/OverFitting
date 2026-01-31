# ==================================================================================
# KAGGLE INDEXING SCRIPT FOR SEG301
# Copy script này vào Kaggle Notebook để chạy Indexing & Merging
# ==================================================================================

import json
import os
import time
import shutil
import psutil
import heapq
from collections import defaultdict
from contextlib import ExitStack
import zipfile

# ----------------------------------------------------------------------------------
# CẤU HÌNH (LƯU Ý SỬA ĐƯỜNG DẪN INPUT)
# ----------------------------------------------------------------------------------
# Trên Kaggle, dữ liệu input thường nằm ở /kaggle/input/tên-dataset/file.jsonl
# Bạn hãy kiểm tra sidebar bên phải của Kaggle để lấy path chính xác
DATA_FILE = "/kaggle/input/vse-data-milestone1/final_data.jsonl"  # <--- SỬA DÒNG NÀY

# Thư mục output (Kaggle cho phép ghi vào /kaggle/working)
OUTPUT_DIR = "/kaggle/working/index_data"
BLOCK_SIZE_LIMIT = 500000 # Kaggle RAM mạnh, có thể để 500k hoặc 1 triệu docs/block

# ----------------------------------------------------------------------------------
# PHẦN 1: SPIMI INDEXER
# ----------------------------------------------------------------------------------
class SPIMIIndexer:
    def __init__(self, data_path, output_dir, block_size_limit=200000):
        self.data_path = data_path
        self.output_dir = output_dir
        self.blocks_dir = os.path.join(output_dir, "blocks")
        self.block_size_limit = block_size_limit
        self.dictionary = defaultdict(list) 
        self.doc_lengths = {} 
        self.doc_offsets = {} 
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
        start_time = time.time()
        
        processed_docs_in_block = 0
        target_fields = ['company_name_seg', 'address_seg', 'industries_str_seg', 'representative_seg']
        
        if not os.path.exists(self.data_path):
            print(f"ERROR: Data file not found at {self.data_path}")
            return

        with open(self.data_path, 'r', encoding='utf-8') as f:
            while True:
                offset = f.tell() 
                line = f.readline()
                if not line:
                    break
                
                try:
                    doc = json.loads(line)
                except:
                    continue
                
                doc_id = self.current_doc_id
                self.doc_offsets[doc_id] = offset
                
                full_text = ""
                for field in target_fields:
                    if field in doc and doc[field]:
                        full_text += " " + str(doc[field])
                
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
        print(f"Indexing finished! Total Docs: {self.current_doc_id}. Time: {time.time() - start_time:.2f}s")

    def save_metadata(self):
        meta_path = os.path.join(self.output_dir, "doc_metadata.json")
        avg_dl = sum(self.doc_lengths.values()) / len(self.doc_lengths) if self.doc_lengths else 0
        metadata = {
            "total_docs": self.current_doc_id,
            "avg_doc_len": avg_dl,
            "doc_lengths": self.doc_lengths,
            "doc_offsets": self.doc_offsets
        }
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f)

# ----------------------------------------------------------------------------------
# PHẦN 2: INDEX MERGER
# ----------------------------------------------------------------------------------
class IndexMerger:
    def __init__(self, blocks_dir, output_file, offsets_file):
        self.blocks_dir = blocks_dir
        self.output_file = output_file
        self.offsets_file = offsets_file

    def parse_line(self, line):
        parts = line.strip().split(' ', 1)
        if len(parts) == 2: return parts[0], parts[1]
        if len(parts) == 1: return parts[0], ""
        return None, None

    def merge(self):
        print(f"Starting merging blocks...")
        block_files = [f for f in os.listdir(self.blocks_dir) if f.startswith("block_") and f.endswith(".txt")]
        block_files.sort()
        
        if not block_files:
            print("No blocks found!")
            return
        
        term_offsets = {}
        with ExitStack() as stack:
            files = [stack.enter_context(open(os.path.join(self.blocks_dir, fn), 'r', encoding='utf-8')) for fn in block_files]
            min_heap = []
            
            for i, f in enumerate(files):
                line = f.readline()
                if line:
                    term, posting = self.parse_line(line)
                    if term: heapq.heappush(min_heap, (term, i, posting))
            
            with open(self.output_file, 'w', encoding='utf-8') as out_f:
                current_term = None
                current_postings = []
                while min_heap:
                    term, block_idx, posting = heapq.heappop(min_heap)
                    if current_term is None: current_term = term
                    
                    if term != current_term:
                        offset = out_f.tell()
                        term_offsets[current_term] = offset
                        out_f.write(f"{current_term} {' '.join(current_postings)}\n")
                        current_term = term
                        current_postings = [posting]
                    else:
                        if posting: current_postings.append(posting)
                    
                    next_line = files[block_idx].readline()
                    if next_line:
                        next_term, next_posting = self.parse_line(next_line)
                        if next_term: heapq.heappush(min_heap, (next_term, block_idx, next_posting))
                
                if current_term:
                    offset = out_f.tell()
                    term_offsets[current_term] = offset
                    out_f.write(f"{current_term} {' '.join(current_postings)}\n")
        
        with open(self.offsets_file, 'w', encoding='utf-8') as f:
            json.dump(term_offsets, f)
        print("Merge completed!")

# ----------------------------------------------------------------------------------
# MAIN EXECUTION
# ----------------------------------------------------------------------------------
if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    # 1. Chạy SPIMI
    print(">>> STEP 1: SPIMI INDEXING")
    indexer = SPIMIIndexer(DATA_FILE, OUTPUT_DIR, block_size_limit=BLOCK_SIZE_LIMIT)
    indexer.index()
    
    # 2. Chạy Merging
    print("\n>>> STEP 2: MERGING BLOCKS")
    BLOCKS_DIR = os.path.join(OUTPUT_DIR, "blocks")
    FINAL_INDEX = os.path.join(OUTPUT_DIR, "inverted_index.txt")
    OFFSETS_FILE = os.path.join(OUTPUT_DIR, "term_offsets.json")
    
    merger = IndexMerger(BLOCKS_DIR, FINAL_INDEX, OFFSETS_FILE)
    merger.merge()
    
    # 3. Nén file để download
    print("\n>>> STEP 3: ZIPPING OUTPUT FOR DOWNLOAD")
    output_zip = "/kaggle/working/vse_index_data.zip"
    
    # Chỉ cần nén 3 file quan trọng, không cần nén thư mục blocks (nặng)
    files_to_zip = [
        "inverted_index.txt",
        "term_offsets.json",
        "doc_metadata.json"
    ]
    
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files_to_zip:
            file_path = os.path.join(OUTPUT_DIR, file)
            if os.path.exists(file_path):
                print(f"Zipping {file}...")
                zipf.write(file_path, arcname=file)
                
    print(f"\nDONE! Download file tại: {output_zip}")
    # Sau khi chạy xong, bạn vào phần 'Data' hoặc 'Output' bên phải để tải file vse_index_data.zip về.
