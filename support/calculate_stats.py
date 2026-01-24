import json
import os
from collections import defaultdict
import re

input_file = r'C:\2nd Disk\SPRING26\SEG301\SEG301-OverFitting\data\milestone1_delivered.jsonl'
output_stats = r'C:\2nd Disk\SPRING26\SEG301\SEG301-OverFitting\support\data_stats.json'

def compute_statistics():
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    stats = {
        'total_documents': 0,
        'has_tax_code': 0,
        'has_address': 0,
        'has_reviews': 0,
        'total_words': 0,
        'vocab': set(),
        'provinces': defaultdict(int),
        'industries': defaultdict(int)
    }

    provinces_list = ['Hà Nội', 'Hồ Chí Minh', 'Đà Nẵng', 'Hải Phòng', 'Cần Thơ', 'Bình Dương', 'Đồng Nai', 'Bắc Ninh']
    
    print(f"Analyzing {input_file}...")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            try:
                item = json.loads(line)
                stats['total_documents'] += 1
                
                # Check tax code
                if item.get('tax_code'):
                    stats['has_tax_code'] += 1
                
                # Check address & province
                addr = item.get('address', '')
                if addr:
                    stats['has_address'] += 1
                    for p in provinces_list:
                        if p.lower() in addr.lower():
                            stats['provinces'][p] += 1
                            break
                
                # Check reviews
                revs = item.get('reviews', [])
                if revs:
                    stats['has_reviews'] += 1
                
                # Text analysis (simple word count)
                # Combine relevant fields for doc length
                text = " ".join([
                    str(item.get('company_name', '')),
                    str(item.get('address', '')),
                    str(item.get('representative', '')),
                    " ".join([ind.get('name', '') for ind in item.get('industries_detail', [])]) if isinstance(item.get('industries_detail'), list) else ""
                ])
                words = text.split()
                stats['total_words'] += len(words)
                
                # Only add to vocab every N items or limit vocab size to avoid memory overflow for 1.8M docs
                if i % 100 == 0:
                     for word in words:
                         if len(word) > 1: # Basic filter
                             stats['vocab'].add(word.lower())
                
                if i % 100000 == 0:
                    print(f"Processed {i} lines...")
                
                # Limit vocab memory
                if len(stats['vocab']) > 1000000:
                    pass # Keep going but vocab is already huge

            except:
                continue

    # Finalize
    result = {
        'total_documents': stats['total_documents'],
        'has_tax_code': stats['has_tax_code'],
        'has_address': stats['has_address'],
        'has_reviews': stats['has_reviews'],
        'avg_doc_length': stats['total_words'] / stats['total_documents'] if stats['total_documents'] > 0 else 0,
        'vocabulary_size': len(stats['vocab']),
        'provinces': dict(stats['provinces']),
    }

    with open(output_stats, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=4)
    
    print(f"Stats saved to {output_stats}")
    print(result)

if __name__ == "__main__":
    compute_statistics()
