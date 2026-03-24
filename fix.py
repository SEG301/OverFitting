with open('src/ranking/bm25.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if 'Documents matched: {len(doc_scores)' in l:
        lines[i] = "        self.last_match_count = len(doc_scores)\n        print(f\"  Documents matched: {self.last_match_count:,}\")\n"

with open('src/ranking/bm25.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)
