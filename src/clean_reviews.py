import json
import os

INPUT_FILE = "data/reviews_itviec.jsonl"
OUTPUT_FILE = "data/reviews_itviec_clean.jsonl"

def clean_text(text):
    if isinstance(text, str):
        # Replace newlines with space and strip extra whitespace
        return text.replace('\n', ' ').strip()
    return text

def clean_data():
    if not os.path.exists(INPUT_FILE):
        print(f"File {INPUT_FILE} does not exist.")
        return

    print(f"Cleaning data from {INPUT_FILE}...")
    count = 0
    with open(INPUT_FILE, 'r', encoding='utf-8') as fin, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as fout:
        
        for line in fin:
            try:
                data = json.loads(line)
                cleaned_data = {k: clean_text(v) for k, v in data.items()}
                fout.write(json.dumps(cleaned_data, ensure_ascii=False) + "\n")
                count += 1
            except json.JSONDecodeError:
                print(f"Skipping invalid JSON line")
    
    print(f"Cleaned {count} records. Saved to {OUTPUT_FILE}.")

if __name__ == "__main__":
    clean_data()
