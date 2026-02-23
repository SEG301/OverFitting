"""
Console Search Application
============================
Milestone 2 - SEG301: Search Engines & Information Retrieval

Chương trình chạy dòng lệnh cho phép:
1. Nhập từ khóa tìm kiếm
2. Trả về kết quả top 10 (hoặc tuỳ chọn)
3. Hiển thị thông tin chi tiết của document

Usage:
    py src/search_console.py
"""

import os
import sys

# Thêm project root vào path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ranking.bm25 import BM25Searcher, display_results


BANNER = r"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║   ███████╗███████╗ ██████╗ ██████╗  ██████╗  ██╗                           ║
║   ██╔════╝██╔════╝██╔════╝ ╚════██╗██╔═══██╗███║                           ║
║   ███████╗█████╗  ██║  ███╗ █████╔╝██║   ██║╚██║                           ║
║   ╚════██║██╔══╝  ██║   ██║ ╚═══██╗██║   ██║ ██║                           ║
║   ███████║███████╗╚██████╔╝██████╔╝╚██████╔╝ ██║                           ║
║   ╚══════╝╚══════╝ ╚═════╝ ╚═════╝  ╚═════╝  ╚═╝                           ║
║                                                                            ║
║   🔍 Vietnamese Enterprise Search Engine                                   ║
║   Milestone 2: SPIMI + BM25 | Team OverFitting                            ║
║                                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
  📖 HƯỚNG DẪN SỬ DỤNG
  ─────────────────────────────────────────────
  Nhập từ khoá để tìm kiếm doanh nghiệp.
  Dữ liệu đã tách từ, dùng gạch dưới cho từ ghép.

  Ví dụ:
    > công_ty công_nghệ
    > bất_động_sản hà_nội
    > xuất_khẩu thủy_sản

  Lệnh:
    :help          Trợ giúp
    :stats         Thống kê index
    :top N         Đặt số kết quả (mặc định 10)
    :quit          Thoát
"""


def main():
    print(BANNER)
    
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    index_dir = os.path.join(project_root, "data", "index")
    jsonl_path = os.path.join(project_root, "data", "milestone1_fixed.jsonl")
    
    # Kiểm tra index
    dict_path = os.path.join(index_dir, "term_dict.pkl")
    if not os.path.exists(dict_path):
        print("⚠️  Index chưa được tạo!")
        print(f"   1. py src/indexer/spimi.py")
        print(f"   2. py src/indexer/merging.py")
        sys.exit(1)
    
    print("🔄 Đang tải index...")
    searcher = BM25Searcher(index_dir=index_dir, jsonl_path=jsonl_path)
    searcher.load_index()
    
    stats = searcher.get_stats()
    print(f"\n✅ Sẵn sàng! {stats['total_documents']:,d} docs | "
          f"{stats['vocabulary_size']:,d} terms")
    print(f"   Nhập :help để xem hướng dẫn.\n")
    
    top_k = 10
    
    while True:
        try:
            query = input("🔍 > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Tạm biệt!")
            break
        
        if not query:
            continue
        
        if query.lower() in (":quit", ":exit", ":q"):
            print("\n👋 Tạm biệt!")
            break
        
        if query.lower() == ":help":
            print(HELP_TEXT)
            continue
        
        if query.lower() == ":stats":
            s = searcher.get_stats()
            print(f"\n📊 Index Statistics:")
            print(f"   Total documents:  {s['total_documents']:,d}")
            print(f"   Vocabulary size:  {s['vocabulary_size']:,d}")
            print(f"   Avg doc length:   {s['avg_document_length']:.1f}")
            print(f"   BM25 k1={s['k1']}, b={s['b']}")
            print(f"   Current top-k:    {top_k}\n")
            continue
        
        if query.lower().startswith(":top "):
            try:
                new_k = int(query.split()[1])
                if 1 <= new_k <= 100:
                    top_k = new_k
                    print(f"   ✅ Top-k = {top_k}\n")
                else:
                    print("   ⚠️ Giá trị 1-100\n")
            except (ValueError, IndexError):
                print("   ⚠️ :top N (ví dụ: :top 20)\n")
            continue
        
        results = searcher.search(query, top_k=top_k)
        display_results(results, query)
    
    searcher.close()


if __name__ == "__main__":
    main()
