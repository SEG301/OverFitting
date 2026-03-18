"""
Index Compression Utilities (Optional)
========================================
Milestone 2 - SEG301

Các kỹ thuật nén để giảm kích thước inverted index:
1. Variable-Byte (VByte) encoding cho doc_id gaps
2. Delta encoding cho postings lists
"""

import struct
from typing import List, Tuple


def vbyte_encode(number: int) -> bytes:
    """
    Mã hóa một số nguyên dương bằng Variable-Byte encoding.
    
    Mỗi byte dùng 7 bit cho data và 1 bit (MSB) làm continuation flag.
    MSB = 1: byte cuối cùng
    MSB = 0: còn bytes tiếp theo
    
    Ví dụ: 
        130 -> 0x02 0x82 (2 bytes thay vì 4 bytes cho int32)
    """
    result = []
    while number >= 128:
        result.append(number & 0x7F)  # 7 lower bits, MSB = 0
        number >>= 7
    result.append(number | 0x80)  # last byte, MSB = 1
    return bytes(result)


def vbyte_decode(data: bytes, offset: int = 0) -> Tuple[int, int]:
    """
    Giải mã một số từ VByte encoding.
    
    Returns:
        (decoded_number, new_offset)
    """
    number = 0
    shift = 0
    while offset < len(data):
        byte = data[offset]
        offset += 1
        if byte & 0x80:  # last byte
            number |= (byte & 0x7F) << shift
            break
        else:
            number |= byte << shift
            shift += 7
    return number, offset


def delta_encode_postings(postings: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Delta encoding cho postings list.
    Lưu gap (khoảng cách) giữa các doc_id thay vì doc_id tuyệt đối.
    
    Ví dụ:
        [(5, 2), (10, 1), (25, 3)] -> [(5, 2), (5, 1), (15, 3)]
    """
    if not postings:
        return []
    
    result = [(postings[0][0], postings[0][1])]
    for i in range(1, len(postings)):
        gap = postings[i][0] - postings[i-1][0]
        result.append((gap, postings[i][1]))
    
    return result


def delta_decode_postings(delta_postings: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Giải mã delta-encoded postings list.
    
    Ví dụ:
        [(5, 2), (5, 1), (15, 3)] -> [(5, 2), (10, 1), (25, 3)]
    """
    if not delta_postings:
        return []
    
    result = [(delta_postings[0][0], delta_postings[0][1])]
    for i in range(1, len(delta_postings)):
        doc_id = result[-1][0] + delta_postings[i][0]
        result.append((doc_id, delta_postings[i][1]))
    
    return result


if __name__ == "__main__":
    # Test VByte encoding
    print("=== VByte Encoding Test ===")
    test_numbers = [1, 5, 127, 128, 255, 1000, 1000000]
    for n in test_numbers:
        encoded = vbyte_encode(n)
        decoded, _ = vbyte_decode(encoded)
        status = "✓" if decoded == n else "✗"
        print(f"  {status} {n:>10,d} -> {len(encoded)} bytes -> {decoded:>10,d}")
    
    # Test Delta encoding
    print("\n=== Delta Encoding Test ===")
    postings = [(5, 2), (10, 1), (25, 3), (100, 1), (250, 2)]
    encoded = delta_encode_postings(postings)
    decoded = delta_decode_postings(encoded)
    print(f"  Original: {postings}")
    print(f"  Encoded:  {encoded}")
    print(f"  Decoded:  {decoded}")
    print(f"  Match:    {'✓' if decoded == postings else '✗'}")
