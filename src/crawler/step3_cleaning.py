import json
import re
import sys
import os
from pathlib import Path

# Add project root to sys.path
root = str(Path(__file__).resolve().parent.parent.parent)
if root not in sys.path:
    sys.path.append(root)

# PATHS
INPUT_FILE = "data/01_deduplicated.jsonl"
OUTPUT_FILE = "data/02_cleaned.jsonl"

def strip_html(text):
    if not text: return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&nbsp;', ' ', text)
    return text.strip()

def fix_case(text):
    if not text: return ""
    if text.isupper() and len(text) > 5:
        return text.title()
    return text

def run():
    print("Step 5: Cleaning Data...")
    count = 0
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f_in, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            try:
                item = json.loads(line)
                # Cleaning logic
                item['company_name'] = fix_case(strip_html(item.get('company_name', '')))
                item['address'] = strip_html(item.get('address', ''))
                
                f_out.write(json.dumps(item, ensure_ascii=False) + '\n')
                count += 1
            except: pass
            
    print(f"DONE Step 5. Cleaned {count} records.")

if __name__ == "__main__":
    run()
