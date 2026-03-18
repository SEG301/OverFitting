"""
Block Merging Algorithm for SPIMI
==================================
Milestone 2 - SEG301: Search Engines & Information Retrieval

Sau khi SPIMI tạo ra nhiều block files (partial inverted indexes),
module này merge tất cả blocks thành một Inverted Index hoàn chỉnh.

Thuật toán Merge:
- Sử dụng K-way merge (tương tự merge sort) nhờ heapq.
- Mở tất cả block files, đọc từng term theo thứ tự alphabet.
- Merge postings lists của cùng một term từ các blocks khác nhau.
- Ghi final inverted index dưới dạng 2 file:
    1. term_dict.pkl: Dict[str, (df, offset, length)] - nhỏ, load nhanh
    2. postings.bin: Binary file chứa postings data - đọc random access

Cấu trúc Final Index:
    term_dict.pkl: Dict[str, Tuple[int, int, int]]
    Trong đó: term -> (document_frequency, byte_offset, byte_length)
    
    postings.bin: Binary file
    Mỗi entry: pickle.dumps([(doc_id, term_freq), ...])
"""

import os
import gc
import sys
import time
import pickle
import heapq
import struct
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DEFAULT_INDEX_DIR = os.path.join(DEFAULT_DATA_PATH, "index")
DEFAULT_BLOCKS_DIR = os.path.join(DEFAULT_INDEX_DIR, "blocks")


# ============================================================================
# K-WAY MERGE
# ============================================================================

class BlockReader:
    """
    Reader cho 1 block file.
    Hỗ trợ đọc từng term theo thứ tự alphabet (iterator pattern).
    """
    
    def __init__(self, block_path: str, block_id: int):
        self.block_id = block_id
        self.block_path = block_path
        self._data = None
        self._iter = None
        self._current = None
    
    def open(self):
        """Load block data từ pickle file."""
        with open(self.block_path, "rb") as f:
            self._data = pickle.load(f)
        # sorted dictionary -> iterator qua (term, postings)
        self._iter = iter(sorted(self._data.items()))
        self._advance()
    
    def _advance(self):
        """Đọc term tiếp theo."""
        try:
            self._current = next(self._iter)
        except StopIteration:
            self._current = None
    
    @property
    def current_term(self) -> Optional[str]:
        """Trả về term hiện tại."""
        if self._current is None:
            return None
        return self._current[0]
    
    @property 
    def current_postings(self) -> Optional[List[Tuple[int, int]]]:
        """Trả về postings list của term hiện tại."""
        if self._current is None:
            return None
        return self._current[1]
    
    @property
    def is_exhausted(self) -> bool:
        """Kiểm tra đã hết data chưa."""
        return self._current is None
    
    def consume(self):
        """Tiêu thụ term hiện tại và chuyển sang term tiếp theo."""
        self._advance()
    
    def close(self):
        """Giải phóng bộ nhớ."""
        self._data = None
        self._iter = None
        self._current = None


def merge_blocks(blocks_dir: str = DEFAULT_BLOCKS_DIR,
                  index_dir: str = DEFAULT_INDEX_DIR) -> str:
    """
    K-way merge tất cả block files thành final inverted index.
    
    Sử dụng kiến trúc 2-file để tối ưu bộ nhớ khi search:
    - term_dict.pkl: Chỉ chứa mapping term -> (df, offset, length), rất nhỏ
    - postings.bin: Chứa postings data, đọc random access khi cần
    
    Ưu điểm: Load nhanh (chỉ cần load term_dict ~50MB thay vì 1GB),
    search nhanh (random file seek cho postings).
    
    Args:
        blocks_dir: Thư mục chứa block files 
        index_dir: Thư mục xuất final index
    
    Returns:
        term_dict_path: Đường dẫn đến term dictionary
    """
    print("=" * 70)
    print("  SPIMI INDEXING - Phase 2: Merging Blocks")
    print("=" * 70)
    
    start_time = time.time()
    
    # Tìm tất cả block files
    block_files = sorted([
        os.path.join(blocks_dir, f) 
        for f in os.listdir(blocks_dir) 
        if f.startswith("block_") and f.endswith(".pkl")
    ])
    
    if not block_files:
        print("ERROR: No block files found!")
        return None
    
    print(f"  Found {len(block_files)} block files to merge")
    
    # Mở tất cả block readers
    readers = []
    for i, path in enumerate(block_files):
        reader = BlockReader(path, i)
        reader.open()
        if not reader.is_exhausted:
            readers.append(reader)
        print(f"  Loaded block {i}: {os.path.basename(path)}")
    
    # Min-heap: (term, block_id) 
    heap = []
    for reader in readers:
        if reader.current_term is not None:
            heapq.heappush(heap, (reader.current_term, reader.block_id))
    
    # Merge và ghi xuống 2 files
    postings_path = os.path.join(index_dir, "postings.bin")
    term_dict = {}  # term -> (df, offset, length)
    
    total_terms = 0
    total_postings = 0
    
    with open(postings_path, "wb") as postings_file:
        while heap:
            # Lấy term nhỏ nhất
            min_term, _ = heap[0]
            
            # Thu thập postings từ tất cả blocks có cùng term này
            merged_postings = []
            
            while heap and heap[0][0] == min_term:
                _, block_id = heapq.heappop(heap)
                
                # Tìm reader tương ứng
                reader = None
                for r in readers:
                    if r.block_id == block_id:
                        reader = r
                        break
                
                if reader and reader.current_term == min_term:
                    merged_postings.extend(reader.current_postings)
                    reader.consume()
                    
                    # Nếu reader chưa hết, đẩy term tiếp theo vào heap
                    if not reader.is_exhausted:
                        heapq.heappush(heap, (reader.current_term, reader.block_id))
            
            # Sắp xếp postings theo doc_id
            merged_postings.sort(key=lambda x: x[0])
            
            # Ghi postings xuống binary file
            doc_freq = len(merged_postings)
            postings_bytes = pickle.dumps(merged_postings, protocol=pickle.HIGHEST_PROTOCOL)
            
            offset = postings_file.tell()
            postings_file.write(postings_bytes)
            length = len(postings_bytes)
            
            # Lưu vào term dictionary
            term_dict[min_term] = (doc_freq, offset, length)
            
            total_terms += 1
            total_postings += doc_freq
            
            if total_terms % 100_000 == 0:
                print(f"  Merged {total_terms:>10,d} terms | "
                      f"Postings: {total_postings:>12,d}")
    
    # Đóng tất cả readers
    for reader in readers:
        reader.close()
    gc.collect()
    
    elapsed = time.time() - start_time
    
    print("-" * 70)
    print(f"  Merge Complete!")
    print(f"  Total unique terms: {total_terms:,d}")
    print(f"  Total postings: {total_postings:,d}")
    print(f"  Time: {elapsed:.1f}s")
    
    # Ghi term dictionary (nhỏ, chỉ chứa term -> (df, offset, length))
    print(f"\n  Writing term dictionary to disk...")
    save_start = time.time()
    
    term_dict_path = os.path.join(index_dir, "term_dict.pkl")
    with open(term_dict_path, "wb") as f:
        pickle.dump(term_dict, f, protocol=pickle.HIGHEST_PROTOCOL)
    
    dict_size_mb = os.path.getsize(term_dict_path) / (1024 * 1024)
    postings_size_mb = os.path.getsize(postings_path) / (1024 * 1024)
    save_time = time.time() - save_start
    
    print(f"  Term dict saved: {term_dict_path} ({dict_size_mb:.1f} MB)")
    print(f"  Postings saved:  {postings_path} ({postings_size_mb:.1f} MB)")
    print(f"  Save time: {save_time:.1f}s")
    print("=" * 70)
    
    return term_dict_path


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    index_dir = os.path.join(data_dir, "index")
    blocks_dir = os.path.join(index_dir, "blocks")
    
    if not os.path.exists(blocks_dir):
        print(f"ERROR: Blocks directory not found: {blocks_dir}")
        print(f"Run spimi.py first to build blocks.")
        sys.exit(1)
    
    final_path = merge_blocks(blocks_dir, index_dir)
    
    if final_path:
        print(f"\n✓ Merge complete. Term dict: {final_path}")
        print(f"  Run search_console.py to start searching!")
