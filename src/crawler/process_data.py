import json
from pathlib import Path
import sys

# Paths
INPUT_FILE = Path("data_member1/speed_data.jsonl")
OUTPUT_FILE = Path("data/clean_data.jsonl")

def dedup_data():
    if not INPUT_FILE.exists():
        print(f"Error: Input file {INPUT_FILE} not found!")
        return

    print(">>> STARTING DEDUPLICATION...")
    print(f"Input: {INPUT_FILE}")
    print(f"Output: {OUTPUT_FILE}")

    seen_tax_codes = set()
    total_rows = 0
    unique_rows = 0
    duplicates = 0

    # Ensure output dir
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(INPUT_FILE, 'r', encoding='utf-8') as fin, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as fout:
        
        for line in fin:
            total_rows += 1
            line = line.strip()
            if not line: continue
            
            try:
                record = json.loads(line)
                tax_code = record.get('tax_code')
                
                # Validation: Tax Code must be present
                if not tax_code:
                    continue
                
                # Normalize Tax Code (remove spaces, etc if needed)
                tax_code = str(tax_code).strip()
                
                if tax_code in seen_tax_codes:
                    duplicates += 1
                else:
                    seen_tax_codes.add(tax_code)
                    # Write clean line
                    fout.write(json.dumps(record, ensure_ascii=False) + '\n')
                    unique_rows += 1
            
            except json.JSONDecodeError:
                continue
            
            if total_rows % 100000 == 0:
                print(f"Processed {total_rows} lines... (Unique: {unique_rows}, Dups: {duplicates})")

    print("\n>>> DEDUPLICATION COMPLETE!")
    print(f"Total processed: {total_rows}")
    print(f"Unique records: {unique_rows}")
    print(f"Duplicates removed: {duplicates}")
    print(f"Saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    dedup_data()
