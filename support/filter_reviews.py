import json
import os

input_file = r'C:\2nd Disk\SPRING26\SEG301\SEG301-OverFitting\data\milestone1_delivered.jsonl'
output_file = r'C:\2nd Disk\SPRING26\SEG301\SEG301-OverFitting\data_sample\sample.jsonl'

samples = []
count = 0

print(f"Scanning {input_file} for companies with reviews...")

with open(input_file, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            data = json.loads(line)
            # Check for fields that might indicate review info
            # Based on common structures, it might be 'reviews', 'rating', 'review_count'
            # or nested in something else.
            has_reviews = False
            
            # Check if 'reviews' exists and is not empty
            if 'reviews' in data and data['reviews'] and len(data['reviews']) > 0:
                has_reviews = True
            # Or if there is a 'rating' or 'review_count' > 0
            elif data.get('review_count', 0) > 0:
                has_reviews = True
            elif data.get('rating', 0) > 0:
                has_reviews = True
                
            if has_reviews:
                samples.append(line)
                count += 1
                if count % 10 == 0:
                    print(f"Found {count} samples...")
            
            if count >= 100:
                break
        except Exception as e:
            continue

if samples:
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(samples)
    print(f"Done! Successfully wrote {len(samples)} samples with reviews to {output_file}")
else:
    print("No companies with reviews found in the scanned portion of the file.")
