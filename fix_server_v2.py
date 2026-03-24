with open('src/ui/server.py', 'r', encoding='utf-8') as f:
    text = f.read()

import re
# Fix the broken text from previous attempt
pattern = r'true_total = len\(results\)\s+if mode == \\\s+vector\\:\s+true_total = len\(vector_searcher\.search\(q, top_k=2000\)\) if vector_loaded else 0\s+if hasattr\(bm25_searcher, \'last_match_count\'\):\s+true_total = bm25_searcher\.last_match_count'

replacement = """true_total = len(results)
    if mode == "vector":
        # Vector search doesn't have a natural 'count', so we simulate it or use the pool
        true_total = len(vector_searcher.search(q, top_k=2000)) if vector_loaded else 0
    elif hasattr(bm25_searcher, 'last_match_count'):
        true_total = bm25_searcher.last_match_count"""

# Using a simpler string replacement since regex failed due to escaping
if 'true_total = len(results)' in text:
    # Find the block starting from true_total = len(results) up to the next return
    new_text = re.sub(r'true_total = len\(results\).*?true_total = bm25_searcher\.last_match_count', replacement, text, flags=re.DOTALL)
    with open('src/ui/server.py', 'w', encoding='utf-8') as f:
        f.write(new_text)
else:
    print("Pattern not found")
