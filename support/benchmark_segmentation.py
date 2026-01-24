import json
import time
from pyvi import ViTokenizer
import os

input_file = r'C:\2nd Disk\SPRING26\SEG301\SEG301-OverFitting\data\milestone1_delivered.jsonl'

def benchmark():
    if not os.path.exists(input_file):
        print("Data file not found for benchmark.")
        return

    sample_size = 5000
    texts = []
    
    print(f"Reading {sample_size} samples...")
    with open(input_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= sample_size: break
            try:
                item = json.loads(line)
                texts.append(item.get('company_name', ''))
                texts.append(item.get('address', ''))
            except: continue

    print(f"Benchmarking PyVi on {len(texts)} strings...")
    start_time = time.time()
    for t in texts:
        ViTokenizer.tokenize(t)
    end_time = time.time()

    duration = end_time - start_time
    # Each line has 2 segments usually (name + address)
    lines_per_second = (len(texts)/2) / duration
    lines_per_minute = lines_per_second * 60

    print(f"Time taken: {duration:.2f} seconds")
    print(f"Speed: ~{lines_per_minute:,.0f} lines/minute")

if __name__ == "__main__":
    benchmark()
