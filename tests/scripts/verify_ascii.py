import json
import unicodedata

# File chuẩn Lần 1
INPUT_FILE = "data/final_data_full_reviews.jsonl"
OUTPUT_TXT = "verify_final_sample_50.txt"

def remove_accents(input_str):
    if not input_str: return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])

def check():
    count = 0
    with open(INPUT_FILE, 'r', encoding='utf-8') as f, open(OUTPUT_TXT, 'w', encoding='utf-8') as out:
        out.write(f"--- CHECKING 50 SAMPLES FROM {INPUT_FILE} ---\n\n")
        for line in f:
            try:
                data = json.loads(line)
                reviews = data.get('reviews', [])
                # Tìm review có nguồn '1900'
                r_1900 = [r for r in reviews if r.get('source') == '1900']
                
                if r_1900:
                    m_name = remove_accents(data.get('company_name', ''))
                    # Lấy tên source
                    s_name = remove_accents(r_1900[0].get('company_name_on_source', ''))
                    addr = remove_accents(data.get('address', ''))
                    
                    out.write(f"[{count+1}]\n")
                    out.write(f"Master Name: {m_name}\n")
                    out.write(f"1900 Name:   {s_name}\n")
                    out.write(f"Address:     {addr}\n")
                    out.write("-" * 40 + "\n")
                    
                    count += 1
                    if count >= 50: break
            except: pass
    print(f"Done. Wrote {count} matches to {OUTPUT_TXT}")

if __name__ == "__main__":
    check()
