import json
import sys

# Set output to utf-8
sys.stdout.reconfigure(encoding='utf-8')

def check():
    with open('data/final_data_with_reviews.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if '"has_review": true' in line:
                data = json.loads(line)
                print(json.dumps(data, ensure_ascii=False, indent=2))
                break

if __name__ == "__main__":
    check()
