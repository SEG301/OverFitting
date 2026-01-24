import json
import re
import os
from pyvi import ViTokenizer

# PATHS
INPUT_FILE = "data/02_cleaned.jsonl"
OUTPUT_FILE = "data/milestone1_final.jsonl"

def safe_segment(text):
    if not text: return ""
    try:
        return ViTokenizer.tokenize(text)
    except:
        return text

def run():
    print("Step 6: Word Segmentation (Vietnamese)...")
    count = 0
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f_in, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            try:
                item = json.loads(line)
                item['company_name_seg'] = safe_segment(item.get('company_name', ''))
                item['address_seg'] = safe_segment(item.get('address', ''))
                
                f_out.write(json.dumps(item, ensure_ascii=False) + '\n')
                count += 1
            except: pass
            
    print(f"DONE Step 6. Final file: {OUTPUT_FILE}")

if __name__ == "__main__":
    run()
