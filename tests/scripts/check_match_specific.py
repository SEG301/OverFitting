import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def check():
    print("--- CHECK CASE: ITVIEC (MB BANK / BOSCH / KMS...) ---")
    
    keywords = ["ngân hàng tmcp quân đội", "bosch", "kms technology"]
    found_count = 0
    
    with open('data/final_data_with_reviews.jsonl', 'r', encoding='utf-8') as f:
        for line in f:
            if '"has_review": true' in line:
                data = json.loads(line)
                name = data.get('company_name', '').lower()
                
                # Check if this company matches one of our famous ITviec samples
                if any(k in name for k in keywords):
                    print(f"\n[MATCH FOUND!]")
                    print(f"Company: {data.get('company_name')}")
                    print(f"Address: {data.get('address')}")
                    print(f"Reviews Count: {len(data.get('reviews', []))}")
                    if data.get('reviews'):
                         print(f"Sample Review: {data['reviews'][0].get('title')} ({data['reviews'][0].get('date')})")
                    found_count += 1
                    if found_count >= 3: break

if __name__ == "__main__":
    check()
