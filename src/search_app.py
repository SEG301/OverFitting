import sys
import os
import json
import time

# Thêm đường dẫn src vào path để import module
sys.path.append(os.path.join(os.path.dirname(__file__)))

from ranking.bm25 import BM25Ranker

class SearchApp:
    def __init__(self, data_file, index_dir):
        self.data_file_path = data_file
        self.index_dir = index_dir
        
        print("Initializing Search Engine...")
        print("1. Loading BM25 Ranker...")
        self.ranker = BM25Ranker(
            index_file=os.path.join(index_dir, "inverted_index.txt"),
            offsets_file=os.path.join(index_dir, "term_offsets.json"),
            metadata_file=os.path.join(index_dir, "doc_metadata.json")
        )
        
        print("2. Loading Document Offsets...")
        # doc_metadata đã được load trong ranker, ta có thể truy cập lại hoặc load riêng
        # Tuy nhiên class BM25Ranker hiện tại không expose offsets ra ngoài, ta nên load lại phần doc_offsets
        # để hiển thị nội dung. Class BM25 chỉ cần doc_lengths.
        with open(os.path.join(index_dir, "doc_metadata.json"), 'r', encoding='utf-8') as f:
            meta = json.load(f)
            self.doc_offsets = {int(k): v for k, v in meta['doc_offsets'].items()}
            
        self.data_file = open(self.data_file_path, 'r', encoding='utf-8')
        print("Search Engine Ready!\n")

    def get_document_content(self, doc_id):
        if doc_id not in self.doc_offsets:
            return None
        
        offset = self.doc_offsets[doc_id]
        self.data_file.seek(offset)
        line = self.data_file.readline()
        try:
            return json.loads(line)
        except:
            return None

    def run(self):
        print("="*60)
        print("SEG301 - VERTICAL SEARCH ENGINE (ENTERPRISE DATA)")
        print("Type 'exit' or 'quit' to stop.")
        print("="*60)
        
        while True:
            try:
                query = input("\nEnter search query: ").strip()
                if query.lower() in ['exit', 'quit']:
                    break
                if not query:
                    continue
                
                # Search
                results, time_taken = self.ranker.search(query, top_k=10)
                
                print(f"\nFound {len(results)} results in {time_taken:.4f} seconds.")
                print("-" * 60)
                
                for i, (doc_id, score) in enumerate(results):
                    content = self.get_document_content(doc_id)
                    title = "Unknown"
                    address = "Unknown"
                    industry = "N/A"
                    
                    if content:
                        title = content.get('company_name', 'No Name')
                        address = content.get('address', 'No Address')
                        # Lấy ngành nghề chính (thường là phần tử đầu tiên trong mảng industries_detail hoặc industries_str_seg)
                        # Ở đây ta lấy industries_str_seg cho gọn, cắt ngắn bớt
                        industries_str = content.get('industries_str_seg', '')
                        if industries_str:
                            industry = industries_str[:100] + "..." if len(industries_str) > 100 else industries_str

                    print(f"#{i+1} [Score: {score:.4f}] {title}")
                    print(f"    Address: {address}")
                    print(f"    Industry: {industry}")
                    print(f"    DocID: {doc_id}")
                    print("-" * 30)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")

    def close(self):
        self.ranker.close()
        self.data_file.close()

if __name__ == "__main__":
    # Cấu hình đường dẫn
    DATA_FILE = r"e:\Crwal\OverFitting\data\final_data.jsonl"
    INDEX_DIR = r"e:\Crwal\OverFitting\data\index_data"
    
    # Kiểm tra dữ liệu nạp
    if not os.path.exists(os.path.join(INDEX_DIR, "inverted_index.txt")):
        print("Error: Index data not found! Please run 'src/indexer/spimi.py' and 'src/indexer/merging.py' first.")
    else:
        app = SearchApp(DATA_FILE, INDEX_DIR)
        try:
            app.run()
        finally:
            app.close()
