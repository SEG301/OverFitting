import json
from pathlib import Path

INPUT_FILE = Path("data_member1/speed_data_v2.jsonl")

# List of all targeted regions (from speed_crawler.py)
TARGETS = [
    "Ha-Noi", "TP-Ho-Chi-Minh", "Da-Nang", "Hai-Phong", "Can-Tho",
    "Bac-Ninh", "Hai-Duong", "Hung-Yen", "Vinh-Phuc", "Quang-Ninh", "Thai-Binh", "Nam-Dinh", "Ninh-Binh", "Ha-Nam", "Phu-Tho", "Bac-Giang", "Thai-Nguyen", "Lang-Son", "Tuyen-Quang", "Yen-Bai", "Lao-Cai", "Ha-Giang", "Cao-Bang", "Bac-Kan", "Dien-Bien", "Lai-Chau", "Son-La", "Hoa-Binh",
    "Thanh-Hoa", "Nghe-An", "Ha-Tinh", "Quang-Binh", "Quang-Tri", "Thua-Thien-Hue", "Quang-Nam", "Quang-Ngai", "Binh-Dinh", "Phu-Yen", "Khanh-Hoa", "Ninh-Thuan", "Binh-Thuan", "Kon-Tum", "Gia-Lai", "Dak-Lak", "Dak-Nong", "Lam-Dong",
    "Binh-Phuoc", "Tay-Ninh", "Binh-Duong", "Dong-Nai", "Ba-Ria-Vung-Tau", "Long-An", "Tien-Giang", "Ben-Tre", "Tra-Vinh", "Vinh-Long", "Dong-Thap", "An-Giang", "Kien-Giang", "Hau-Giang", "Soc-Trang", "Bac-Lieu", "Ca-Mau"
]

def check_progress():
    if not INPUT_FILE.exists():
        print("File v2 not found. Maybe crawler hasn't saved anything yet?")
        return

    found_regions = set()
    print("Scanning file... (This relies on URL pattern matching)")
    
    line_count = 0
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line_count += 1
            if line_count % 100000 == 0: print(f"Scanned {line_count} lines...")
            try:
                # Quick scan without full json load for speed? No, verify json integrity
                data = json.loads(line)
                url = data.get('url', '')
                # URL structure: https://.../Region-Name/trang-X/
                # Check which region is in URL
                for t in TARGETS:
                    if f"/{t}/" in url or f"/{t.replace('-',' ')}/" in url:
                        found_regions.add(t)
                        # Don't break, maybe overlap
            except: pass

    print("-" * 30)
    print(f"Total Lines in V2: {line_count}")
    print(f"Regions Covered: {len(found_regions)} / {len(TARGETS)}")
    
    missing = [t for t in TARGETS if t not in found_regions]
    if missing:
        print("\n>>> MISSING REGIONS (NOT STARTED or NO DATA):")
        print(", ".join(missing))
    else:
        print("\n>>> ALL REGIONS COVERED! YOU CAN STOP NOW.")

if __name__ == "__main__":
    check_progress()
