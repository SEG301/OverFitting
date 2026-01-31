import json
import math
import time
import os

class BM25Ranker:
    def __init__(self, index_file, offsets_file, metadata_file, k1=1.2, b=0.1):
        """
        Args:
            index_file: Đường dẫn file inverted_index.txt
            offsets_file: Đường dẫn file term_offsets.json
            metadata_file: Đường dẫn file doc_metadata.json
            k1, b: Tham số chuẩn của BM25.
        """
        self.index_file_path = index_file
        self.k1 = k1
        self.b = b
        
        # Load Metadata
        print("Loading metadata...")
        with open(metadata_file, 'r', encoding='utf-8') as f:
            meta = json.load(f)
            self.total_docs = meta['total_docs']
            self.avgdl = meta['avg_doc_len']
            self.doc_lengths = {int(k): v for k, v in meta['doc_lengths'].items()}
            
        # Load Term Offsets
        print("Loading term offsets...")
        with open(offsets_file, 'r', encoding='utf-8') as f:
            self.term_offsets = json.load(f)
            
        self.index_file = open(self.index_file_path, 'r', encoding='utf-8')
        print("BM25 Ranker ready.")

    def tokenize(self, text):
        # Đồng bộ logic với Indexer: Bỏ _ TRƯỚC khi split để tách hẳn thành các từ đơn
        text = text.lower().replace('_', ' ')
        return text.split()

    def get_postings(self, term):
        """
        Lấy danh sách postings cho 1 term.
        Trả về: Dictionary {doc_id: freq}
        """
        if term not in self.term_offsets:
            return {}
        
        offset = self.term_offsets[term]
        self.index_file.seek(offset)
        line = self.index_file.readline()
        
        parts = line.strip().split()
        # parts[0] là term, từ parts[1] là doc_id:freq
        postings = {}
        for p in parts[1:]:
            try:
                doc_id_str, freq_str = p.split(':')
                postings[int(doc_id_str)] = int(freq_str)
            except ValueError:
                continue
        return postings

    def compute_idf(self, doc_freq):
        # Công thức IDF chuẩn cho BM25
        # idf = log( (N - n + 0.5) / (n + 0.5) + 1 )
        return math.log((self.total_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1)

    def search(self, query, top_k=10):
        start_time = time.time()
        query_terms = self.tokenize(query)
        scores = {} # doc_id -> score
        
        for term in query_terms:
            postings = self.get_postings(term)
            if not postings:
                continue
            
            doc_freq = len(postings)
            idf = self.compute_idf(doc_freq)
            
            for doc_id, tf in postings.items():
                doc_len = self.doc_lengths.get(doc_id, self.avgdl)
                
                # BM25 Component
                # num = tf * (k1 + 1)
                # den = tf + k1 * (1 - b + b * (dl / avgdl))
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
                
                score = idf * (numerator / denominator)
                
                if doc_id in scores:
                    scores[doc_id] += score
                else:
                    scores[doc_id] = score
        
        # Sort scores descending
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        
        elapsed = time.time() - start_time
        return sorted_results, elapsed

    def close(self):
        self.index_file.close()

if __name__ == "__main__":
    # Test nhanh
    BASE_DIR = r"e:\Crwal\OverFitting\data\index_data"
    ranker = BM25Ranker(
        index_file=os.path.join(BASE_DIR, "inverted_index.txt"),
        offsets_file=os.path.join(BASE_DIR, "term_offsets.json"),
        metadata_file=os.path.join(BASE_DIR, "doc_metadata.json")
    )
    
    query = "công ty sản xuất"
    print(f"\nSearching for: '{query}'")
    results, time_taken = ranker.search(query)
    
    print(f"Found {len(results)} results in {time_taken:.4f}s")
    for doc_id, score in results:
        print(f"DocID: {doc_id} - Score: {score:.4f}")
        
    ranker.close()
