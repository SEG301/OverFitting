"""
Unit Tests for SPIMI Algorithm
================================
"""

import os
import sys
import json
import shutil
import pickle
import tempfile
import unittest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.indexer.spimi import tokenize, spimi_invert, write_block_to_disk


class TestTokenize(unittest.TestCase):
    """Test tokenizer function."""
    
    def test_basic_tokenization(self):
        text = "công_ty tnhh thương_mại dịch_vụ"
        tokens = tokenize(text)
        self.assertEqual(tokens, ["công_ty", "tnhh", "thương_mại", "dịch_vụ"])
    
    def test_filters_short_tokens(self):
        text = "a b công_ty c d"
        tokens = tokenize(text)
        self.assertNotIn("a", tokens)
        self.assertNotIn("b", tokens)
        self.assertIn("công_ty", tokens)
    
    def test_filters_special_chars(self):
        text = "công_ty ... --- !!!"
        tokens = tokenize(text)
        self.assertEqual(tokens, ["công_ty"])
    
    def test_keeps_numbers(self):
        text = "mã_số 0123456789"
        tokens = tokenize(text)
        self.assertIn("0123456789", tokens)
    
    def test_empty_input(self):
        tokens = tokenize("")
        self.assertEqual(tokens, [])


class TestSPIMIInvert(unittest.TestCase):
    """Test SPIMI-Invert algorithm."""
    
    def test_basic_invert(self):
        token_stream = [
            ("apple", 1), ("banana", 1), ("apple", 2),
            ("cherry", 2), ("apple", 1), ("banana", 3)
        ]
        result = spimi_invert(token_stream)
        
        # apple appears in doc 1 (tf=2) and doc 2 (tf=1)
        self.assertIn("apple", result)
        self.assertEqual(result["apple"], [(1, 2), (2, 1)])
        
        # banana appears in doc 1 (tf=1) and doc 3 (tf=1)
        self.assertIn("banana", result)
        self.assertEqual(result["banana"], [(1, 1), (3, 1)])
    
    def test_empty_stream(self):
        result = spimi_invert([])
        self.assertEqual(result, {})
    
    def test_postings_sorted_by_docid(self):
        token_stream = [("term", 5), ("term", 2), ("term", 8), ("term", 1)]
        result = spimi_invert(token_stream)
        doc_ids = [doc_id for doc_id, _ in result["term"]]
        self.assertEqual(doc_ids, sorted(doc_ids))


class TestWriteBlock(unittest.TestCase):
    """Test block writing to disk."""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_write_and_read_block(self):
        block_index = {
            "apple": [(1, 2), (2, 1)],
            "banana": [(1, 1), (3, 1)],
        }
        
        path = write_block_to_disk(block_index, 0, self.test_dir)
        
        self.assertTrue(os.path.exists(path))
        
        with open(path, "rb") as f:
            loaded = pickle.load(f)
        
        self.assertEqual(loaded["apple"], [(1, 2), (2, 1)])
        self.assertEqual(loaded["banana"], [(1, 1), (3, 1)])
    
    def test_terms_sorted_in_block(self):
        block_index = {
            "cherry": [(1, 1)],
            "apple": [(2, 1)],
            "banana": [(3, 1)],
        }
        
        path = write_block_to_disk(block_index, 0, self.test_dir)
        
        with open(path, "rb") as f:
            loaded = pickle.load(f)
        
        keys = list(loaded.keys())
        self.assertEqual(keys, sorted(keys))


if __name__ == "__main__":
    unittest.main(verbosity=2)
