with open('src/ui/server.py', 'r', encoding='utf-8') as f:
    text = f.read()
import re
text = re.sub(r'true_total = len\(results\)', r'true_total = len(results)\n    if mode == \
vector\:\n        true_total = len(vector_searcher.search(q, top_k=2000)) if vector_loaded else 0', text)
with open('src/ui/server.py', 'w', encoding='utf-8') as f:
    f.write(text)
