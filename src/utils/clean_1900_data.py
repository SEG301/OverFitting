import json
import os

INPUT_FILE = "data/reviews_1900_detailed.jsonl"
OUTPUT_FILE = "data/reviews_1900_detailed_cleaned.jsonl"

def clean_string(s):
    if not isinstance(s, str):
        return s
    # Remove \r, \n, and " characters as requested
    # Replacing newlines with space to avoid word concatenation often makes sense, 
    # but the user said "xóa" (delete). 
    # However, "hello\nworld" -> "helloworld" is usually bad. 
    # I will replace \n and \r with a single space.
    s = s.replace('\r', ' ').replace('\n', ' ')
    
    # Remove double quotes (") 
    s = s.replace('"', '')
    
    # Clean up multiple spaces
    s = " ".join(s.split())
    
    # Remove leading hyphen if present (often used as bullet point)
    if s.startswith('- '):
        s = s[2:]
    elif s.startswith('-'):
        s = s[1:]
        
    return s.strip()

def clean_data(data):
    if isinstance(data, dict):
        # Remove 'crawled_at' if it exists at top level (or any level)
        if 'crawled_at' in data:
            del data['crawled_at']
            
        for k, v in data.items():
            data[k] = clean_data(v)
    elif isinstance(data, list):
        return [clean_data(item) for item in data]
    elif isinstance(data, str):
        return clean_string(data)
    
    return data

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"File {INPUT_FILE} not found.")
        return

    print(f"Cleaning {INPUT_FILE}...")
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as fin, \
         open(OUTPUT_FILE, 'w', encoding='utf-8') as fout:
        
        count = 0
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                cleaned_record = clean_data(record)
                fout.write(json.dumps(cleaned_record, ensure_ascii=False) + "\n")
                count += 1
            except Exception as e:
                print(f"Error processing line: {e}")

    print(f"Finished cleaning. Processed {count} records.")
    print(f"Saved to {OUTPUT_FILE}")
    
    # Replace the original file with the cleaned one?
    # The user asked to "chuẩn hóa lại dữ liệu file reviews_1900_detailed.jsonl"
    # implying the file itself should be updated.
    os.replace(OUTPUT_FILE, INPUT_FILE)
    print(f"Replaced original file with cleaned version.")

if __name__ == "__main__":
    main()
