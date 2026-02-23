"""
SPIMI (Single-Pass In-Memory Indexing) Algorithm Implementation
================================================================
Milestone 2 - SEG301: Search Engines & Information Retrieval

Thuật toán SPIMI:
1. Đọc documents theo từng block (batch) để tránh tràn RAM.
2. Với mỗi block, xây dựng một Inverted Index tạm (in-memory dictionary).
3. Khi dictionary đạt giới hạn kích thước (hoặc hết block) -> sắp xếp terms 
   và ghi xuống đĩa thành 1 file block.
4. Sau khi xử lý hết tất cả documents, merge các block files thành 
   một Inverted Index hoàn chỉnh.

Cấu trúc Inverted Index:
    term -> [doc_freq, [(doc_id, term_freq), (doc_id, term_freq), ...]]
"""

import json
import os
import sys
import gc
import time
import struct
import pickle
import tempfile
from collections import defaultdict
from typing import Dict, List, Tuple, Generator, Optional


# ============================================================================
# CONFIGURATION
# ============================================================================

# Số documents mỗi block (điều chỉnh tùy RAM)
BLOCK_SIZE = 50_000

# Thư mục lưu các block tạm và index cuối cùng
DEFAULT_DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data")
DEFAULT_INDEX_DIR = os.path.join(DEFAULT_DATA_PATH, "index")
DEFAULT_BLOCKS_DIR = os.path.join(DEFAULT_INDEX_DIR, "blocks")


# ============================================================================
# DOCUMENT READER
# ============================================================================

def read_documents(jsonl_path: str, batch_size: int = BLOCK_SIZE) -> Generator:
    """
    Đọc documents từ file JSONL theo batch.
    
    Mỗi document sẽ được tạo thành một chuỗi text bao gồm các trường 
    đã được tách từ (segmented) để phục vụ indexing.
    
    Lưu byte_offset của từng dòng để có thể random access sau này
    (thay vì lưu toàn bộ metadata vào RAM).
    
    Yields:
        batch: List of (doc_id, text, byte_offset) tuples
    """
    batch = []
    doc_id = 0
    
    # Đọc ở binary mode để f.tell() trả về byte offset chính xác
    # (text mode trên Windows với UTF-8 encoding rất chậm với tell())
    with open(jsonl_path, "rb") as f:
        while True:
            byte_offset = f.tell()
            raw_line = f.readline()
            if not raw_line:
                break
            
            line = raw_line.decode("utf-8", errors="ignore").strip()
            if not line:
                continue
            
            try:
                doc = json.loads(line)
            except json.JSONDecodeError:
                continue
            
            # Tạo text tìm kiếm từ các trường đã segmented
            # Ưu tiên dùng trường _seg (đã tách từ tiếng Việt)
            text_parts = []
            
            # Tên công ty (trọng số cao - lặp lại để tăng TF)
            company_seg = doc.get("company_name_seg", "")
            if company_seg:
                text_parts.append(company_seg)
                text_parts.append(company_seg)  # boost tên công ty
            
            # Địa chỉ
            addr_seg = doc.get("address_seg", "")
            if addr_seg:
                text_parts.append(addr_seg)
            
            # Người đại diện
            rep_seg = doc.get("representative_seg", "")
            if rep_seg:
                text_parts.append(rep_seg)
            
            # Tình trạng hoạt động
            status_seg = doc.get("status_seg", "")
            if status_seg:
                text_parts.append(status_seg)
            
            # Ngành nghề kinh doanh (trọng số cao)
            industries_seg = doc.get("industries_str_seg", "")
            if industries_seg:
                text_parts.append(industries_seg)
                text_parts.append(industries_seg)  # boost ngành nghề
            
            text = " ".join(text_parts).lower()
            
            if not text.strip():
                doc_id += 1
                continue
            
            batch.append((doc_id, text, byte_offset))
            doc_id += 1
            
            if len(batch) >= batch_size:
                yield batch
                batch = []
    
    if batch:
        yield batch


# ============================================================================
# TOKENIZER
# ============================================================================

def tokenize(text: str) -> List[str]:
    """
    Tokenize text đã được tách từ (word segmented).
    
    Vì dữ liệu đã qua word segmentation (từ Milestone 1), các từ ghép 
    tiếng Việt đã được nối bằng dấu gạch dưới (ví dụ: "công_ty", "hà_nội").
    
    Chỉ cần split theo khoảng trắng và lọc stopwords/ký tự đặc biệt.
    """
    tokens = text.split()
    # Lọc tokens quá ngắn hoặc chỉ chứa ký tự đặc biệt
    result = []
    for token in tokens:
        # Bỏ qua tokens quá ngắn (1 ký tự) trừ khi là số
        if len(token) <= 1 and not token.isdigit():
            continue
        # Bỏ qua tokens chỉ chứa ký tự đặc biệt
        if all(c in '.,;:!?()-_/\\|@#$%^&*+=<>{}[]"\'~`' for c in token):
            continue
        result.append(token)
    
    return result


# ============================================================================
# SPIMI CORE ALGORITHM
# ============================================================================

def spimi_invert(token_stream: List[Tuple[str, int]]) -> Dict[str, List[int]]:
    """
    SPIMI-Invert: Xây dựng inverted index cho 1 block trong RAM.
    
    Khác với BSB Index cổ điển (cần preallocate postings lists), 
    SPIMI sử dụng dynamic dictionary và tự mở rộng postings lists.
    
    Args:
        token_stream: List of (term, doc_id) pairs
    
    Returns:
        dictionary: Dict mapping term -> list of (doc_id, term_freq) tuples
    """
    dictionary = defaultdict(lambda: defaultdict(int))
    
    for term, doc_id in token_stream:
        dictionary[term][doc_id] += 1
    
    # Chuyển đổi sang format [(doc_id, tf), ...]
    result = {}
    for term in dictionary:
        postings = sorted(dictionary[term].items())  # sắp xếp theo doc_id
        result[term] = postings
    
    return result


def write_block_to_disk(block_index: Dict[str, List[Tuple[int, int]]], 
                         block_num: int, 
                         blocks_dir: str) -> str:
    """
    Ghi một block index xuống đĩa.
    
    Format: Mỗi block file là một pickle chứa dictionary đã sắp xếp terms.
    Terms được sắp xếp theo thứ tự alphabet để hỗ trợ merge nhanh.
    
    Args:
        block_index: Inverted index của block
        block_num: Số thứ tự block
        blocks_dir: Thư mục lưu blocks
    
    Returns:
        block_path: Đường dẫn file block đã ghi
    """
    os.makedirs(blocks_dir, exist_ok=True)
    block_path = os.path.join(blocks_dir, f"block_{block_num:04d}.pkl")
    
    # Sắp xếp terms theo alphabet
    sorted_index = dict(sorted(block_index.items()))
    
    with open(block_path, "wb") as f:
        pickle.dump(sorted_index, f, protocol=pickle.HIGHEST_PROTOCOL)
    
    return block_path


def build_spimi_index(jsonl_path: str, 
                       blocks_dir: str = DEFAULT_BLOCKS_DIR,
                       block_size: int = BLOCK_SIZE) -> Tuple[List[str], int, Dict]:
    """
    Giai đoạn 1: Chia documents thành blocks và tạo partial inverted index.
    
    Quy trình:
    1. Đọc documents theo batch (block_size docs mỗi batch)
    2. Với mỗi batch: tokenize -> tạo token stream -> SPIMI-Invert -> ghi disk
    3. Giải phóng RAM sau mỗi block (gc.collect())
    4. Lưu doc_offsets (doc_id -> byte_offset) thay vì metadata (tiết kiệm RAM)
    
    Args:
        jsonl_path: Đường dẫn đến file JSONL
        blocks_dir: Thư mục lưu block files
        block_size: Số documents mỗi block
    
    Returns:
        block_files: Danh sách đường dẫn các block files
        total_docs: Tổng số documents đã index
        doc_lengths: Dict mapping doc_id -> document length (số terms)
    """
    print("=" * 70)
    print("  SPIMI INDEXING - Phase 1: Building Block Indexes")
    print("=" * 70)
    
    block_files = []
    block_num = 0
    total_docs = 0
    doc_lengths = {}      # doc_id -> số lượng terms trong document
    doc_offsets = {}       # doc_id -> byte offset trong file JSONL
    
    start_time = time.time()
    
    for batch in read_documents(jsonl_path, batch_size=block_size):
        block_start = time.time()
        
        # Tạo token stream cho block này
        token_stream = []
        for doc_id, text, byte_offset in batch:
            tokens = tokenize(text)
            doc_lengths[doc_id] = len(tokens)
            doc_offsets[doc_id] = byte_offset  # Chỉ lưu byte offset (8 bytes/doc)
            
            for token in tokens:
                token_stream.append((token, doc_id))
            
            total_docs += 1
        
        # SPIMI-Invert
        block_index = spimi_invert(token_stream)
        
        # Ghi block xuống đĩa
        block_path = write_block_to_disk(block_index, block_num, blocks_dir)
        block_files.append(block_path)
        
        block_time = time.time() - block_start
        vocab_size = len(block_index)
        
        print(f"  Block {block_num:4d} | "
              f"Docs: {total_docs:>10,d} | "
              f"Vocab: {vocab_size:>8,d} | "
              f"Time: {block_time:.1f}s")
        
        # Giải phóng RAM
        del token_stream
        del block_index
        gc.collect()
        
        block_num += 1
    
    elapsed = time.time() - start_time
    
    print("-" * 70)
    print(f"  Phase 1 Complete!")
    print(f"  Total documents: {total_docs:,d}")
    print(f"  Total blocks: {block_num}")
    print(f"  Time: {elapsed:.1f}s ({total_docs / elapsed:.0f} docs/sec)")
    print("=" * 70)
    
    index_dir = os.path.dirname(blocks_dir)
    
    # Lưu document offsets (nhỏ gọn: chỉ dict[int, int])
    offsets_path = os.path.join(index_dir, "doc_offsets.pkl")
    with open(offsets_path, "wb") as f:
        pickle.dump(doc_offsets, f, protocol=pickle.HIGHEST_PROTOCOL)
    offsets_size = os.path.getsize(offsets_path) / (1024 * 1024)
    print(f"  Saved doc offsets: {offsets_path} ({offsets_size:.1f} MB)")
    
    # Lưu document lengths
    lengths_path = os.path.join(index_dir, "doc_lengths.pkl")
    with open(lengths_path, "wb") as f:
        pickle.dump(doc_lengths, f, protocol=pickle.HIGHEST_PROTOCOL)
    lengths_size = os.path.getsize(lengths_path) / (1024 * 1024)
    print(f"  Saved doc lengths: {lengths_path} ({lengths_size:.1f} MB)")
    
    return block_files, total_docs, doc_lengths


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Đường dẫn mặc định
    data_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    jsonl_path = os.path.join(data_dir, "milestone1_fixed.jsonl")
    index_dir = os.path.join(data_dir, "index")
    blocks_dir = os.path.join(index_dir, "blocks")
    
    if not os.path.exists(jsonl_path):
        print(f"ERROR: Data file not found: {jsonl_path}")
        sys.exit(1)
    
    print(f"\nData file: {jsonl_path}")
    print(f"Index directory: {index_dir}")
    print(f"Block size: {BLOCK_SIZE:,d} documents\n")
    
    # Phase 1: Build blocks
    block_files, total_docs, doc_lengths = build_spimi_index(
        jsonl_path, blocks_dir, BLOCK_SIZE
    )
    
    print(f"\n✓ Phase 1 done. Run merging.py next to merge blocks.")
