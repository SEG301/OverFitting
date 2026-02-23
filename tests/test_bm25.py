"""
Unit Tests for BM25 Ranking Algorithm
=======================================
"""

import os
import sys
import math
import unittest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.ranking.bm25 import BM25Searcher


class TestBM25Math(unittest.TestCase):
    """Test BM25 mathematical computations."""
    
    def setUp(self):
        """Tạo fake searcher với dữ liệu test nhỏ."""
        self.searcher = BM25Searcher.__new__(BM25Searcher)
        self.searcher.k1 = 1.2
        self.searcher.b = 0.75
        self.searcher.total_docs = 100
        self.searcher.avg_doc_length = 50.0
        self.searcher.vocab_size = 10
        self.searcher.postings_file = None
        
        # Fake term dictionary: term -> (df, offset, length)
        # offset and length are not used in unit tests (no actual postings file)
        self.searcher.term_dict = {
            "python": (10, 0, 0),     # df=10
            "java":   (50, 0, 0),     # df=50
            "rare":   (1,  0, 0),     # df=1 (hiếm)
            "common": (99, 0, 0),     # df=99 (phổ biến)
        }
        
        self.searcher.doc_lengths = {i: 50 for i in range(100)}
        self.searcher.doc_metadata = {i: {"company_name": f"Doc {i}"} for i in range(100)}
        self.searcher._loaded = True
    
    def test_idf_rare_term_higher(self):
        """Term hiếm (df nhỏ) phải có IDF cao hơn term phổ biến."""
        idf_rare = self.searcher.compute_idf("rare")       # df=1
        idf_common = self.searcher.compute_idf("common")   # df=99
        
        self.assertGreater(idf_rare, idf_common)
    
    def test_idf_unknown_term(self):
        """Term không tồn tại phải có IDF = 0."""
        idf = self.searcher.compute_idf("nonexistent")
        self.assertEqual(idf, 0.0)
    
    def test_idf_formula_correctness(self):
        """Kiểm tra công thức IDF: log((N - df + 0.5) / (df + 0.5) + 1)."""
        N = 100
        df = 10
        expected_idf = math.log((N - df + 0.5) / (df + 0.5) + 1)
        actual_idf = self.searcher.compute_idf("python")
        
        self.assertAlmostEqual(actual_idf, expected_idf, places=6)
    
    def test_tf_component_saturation(self):
        """TF cao hơn cho score cao hơn, nhưng có giới hạn (saturation)."""
        doc_len = 50
        
        tf1 = self.searcher.compute_tf_component(1, doc_len)
        tf5 = self.searcher.compute_tf_component(5, doc_len)
        tf100 = self.searcher.compute_tf_component(100, doc_len)
        
        # tf tăng -> score tăng
        self.assertGreater(tf5, tf1)
        self.assertGreater(tf100, tf5)
        
        # Nhưng tốc độ tăng giảm dần (saturation)
        diff_1_to_5 = tf5 - tf1
        diff_5_to_100 = tf100 - tf5
        ratio = diff_5_to_100 / diff_1_to_5
        self.assertLess(ratio, 1.0)  # tăng chậm hơn
    
    def test_length_normalization(self):
        """Document ngắn hơn (cùng tf) phải có TF component cao hơn."""
        tf = 3
        short_doc = self.searcher.compute_tf_component(tf, 20)   # doc ngắn
        long_doc = self.searcher.compute_tf_component(tf, 200)   # doc dài
        
        self.assertGreater(short_doc, long_doc)
    
    def test_search_empty_query(self):
        """Query rỗng phải trả về list rỗng."""
        results = self.searcher.search("")
        self.assertEqual(results, [])
    
    def test_search_nonexistent_term(self):
        """Query với term không tồn tại phải trả về list rỗng."""
        results = self.searcher.search("xyznonexistent")
        self.assertEqual(results, [])


class TestBM25Tokenizer(unittest.TestCase):
    """Test BM25 query tokenizer."""
    
    def setUp(self):
        self.searcher = BM25Searcher.__new__(BM25Searcher)
        self.searcher.postings_file = None
    
    def test_lowercase(self):
        tokens = self.searcher._tokenize_query("CÔNG_TY ABC")
        self.assertEqual(tokens, ["công_ty", "abc"])
    
    def test_filter_single_chars(self):
        tokens = self.searcher._tokenize_query("a b c abc")
        self.assertNotIn("a", tokens)
        self.assertIn("abc", tokens)


if __name__ == "__main__":
    unittest.main(verbosity=2)
