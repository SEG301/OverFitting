import json
import time
import logging
from typing import List

logger = logging.getLogger("SuggestionService")

class TrieNode:
    __slots__ = ['children', 'company_names']
    def __init__(self):
        self.children = {}
        self.company_names = [] # caches top N full names at each intermediate node

class SuggestionService:
    """
    In-memory Trie for ultra-fast prefix-based Autocomplete of Company Names.
    Uses __slots__ and intermediate caching to ensure low latency and lower memory footprint.
    """
    def __init__(self):
        self.root = TrieNode()
        self.is_loaded = False
        self.cache_limit = 5

    def build_from_jsonl(self, jsonl_path: str, max_docs: int = 2000000):
        """
        Builds the Trie iteratively and also builds an O(1) byte offset map for lookup.
        """
        logger.info(f"Building Autocomplete Trie and ID Offsets from {jsonl_path}...")
        t0 = time.time()
        count = 0
        self.id_offsets = {}
        try:
            with open(jsonl_path, 'rb') as f:
                while True:
                    offset = f.tell()
                    line = f.readline()
                    if not line:
                        break
                        
                    try:
                        doc = json.loads(line.decode('utf-8', errors='ignore'))
                        
                        # Fast Offset Dictionary Map for ALL entries
                        uid = doc.get("url") or doc.get("tax_code") or doc.get("id") or doc.get("doc_id")
                        if uid:
                            self.id_offsets[str(uid)] = offset
                            
                        # Only feed top max_docs into Autocomplete engine to save Memory
                        if count < max_docs:
                            name = doc.get("company_name", "").strip()
                            if name:
                                self._insert(name)
                                
                        count += 1
                    except Exception:
                        continue
            self.is_loaded = True
            logger.info(f"Trie/Map built with {count} companies in {time.time() - t0:.2f}s")
        except FileNotFoundError:
            logger.warning(f"File {jsonl_path} not found. Trie is empty.")

    def _insert(self, name: str):
        node = self.root
        lowered = name.lower()
        
        for char in lowered:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
            
            # Cache the original name early up the tree so we don't have to DFS at query time
            if len(node.company_names) < self.cache_limit and name not in node.company_names:
                node.company_names.append(name)

    def suggest(self, prefix: str) -> List[str]:
        """Returns autocomplete suggestions matching the prefix in O(K) where K = len(prefix)"""
        if not prefix or not self.is_loaded:
            return []
            
        node = self.root
        for char in prefix.lower():
            if char not in node.children:
                return []
            node = node.children[char]
            
        return node.company_names
