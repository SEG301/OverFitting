import os
import heapq
import json
from contextlib import ExitStack

class IndexMerger:
    def __init__(self, blocks_dir, output_file, offsets_file):
        """
        Args:
            blocks_dir: Thư mục chứa các file block_*.txt
            output_file: Đường dẫn file output inverted index hoàn chỉnh.
            offsets_file: Đường dẫn file lưu vị trí byte của từng term (để search nhanh).
        """
        self.blocks_dir = blocks_dir
        self.output_file = output_file
        self.offsets_file = offsets_file

    def parse_line(self, line):
        """
        Parse một dòng trong file block.
        Format: term doc_id:tf doc_id:tf ...
        Trả về: (term, posting_string)
        """
        parts = line.strip().split(' ', 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        elif len(parts) == 1:
            return parts[0], ""
        return None, None

    def merge(self):
        print(f"Starting merging blocks from {self.blocks_dir}...")
        
        block_files = [f for f in os.listdir(self.blocks_dir) if f.startswith("block_") and f.endswith(".txt")]
        block_files.sort()
        
        if not block_files:
            print("No blocks found to merge!")
            return

        print(f"Found {len(block_files)} blocks.")
        
        term_offsets = {}
        
        with ExitStack() as stack:
            files = [stack.enter_context(open(os.path.join(self.blocks_dir, fn), 'r', encoding='utf-8')) for fn in block_files]
            
            min_heap = []
            
            # Khởi tạo heap
            for i, f in enumerate(files):
                line = f.readline()
                if line:
                    term, posting = self.parse_line(line)
                    if term:
                        heapq.heappush(min_heap, (term, i, posting))
            
            with open(self.output_file, 'w', encoding='utf-8') as out_f:
                current_term = None
                current_postings = []
                
                while min_heap:
                    term, block_idx, posting = heapq.heappop(min_heap)
                    
                    if current_term is None:
                        current_term = term
                    
                    if term != current_term:
                        # Lưu offset trước khi ghi
                        offset = out_f.tell()
                        term_offsets[current_term] = offset
                        
                        full_posting = " ".join(current_postings)
                        out_f.write(f"{current_term} {full_posting}\n")
                        
                        current_term = term
                        current_postings = [posting]
                    else:
                        if posting:
                            current_postings.append(posting)
                    
                    next_line = files[block_idx].readline()
                    if next_line:
                        next_term, next_posting = self.parse_line(next_line)
                        if next_term:
                            heapq.heappush(min_heap, (next_term, block_idx, next_posting))
                
                # Ghi term cuối
                if current_term:
                    offset = out_f.tell()
                    term_offsets[current_term] = offset
                    
                    full_posting = " ".join(current_postings)
                    out_f.write(f"{current_term} {full_posting}\n")
        
        # Lưu file offsets
        print(f"Saving term offsets map to {self.offsets_file}...")
        with open(self.offsets_file, 'w', encoding='utf-8') as f:
            json.dump(term_offsets, f)
                    
        print(f"Merge completed! Output saved to: {self.output_file}")

if __name__ == "__main__":
    BLOCKS_DIR = r"e:\Crwal\OverFitting\data\index_data\blocks"
    OUTPUT_FILE = r"e:\Crwal\OverFitting\data\index_data\inverted_index.txt"
    OFFSETS_FILE = r"e:\Crwal\OverFitting\data\index_data\term_offsets.json"
    
    merger = IndexMerger(BLOCKS_DIR, OUTPUT_FILE, OFFSETS_FILE)
    merger.merge()
