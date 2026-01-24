import requests
from bs4 import BeautifulSoup
import json
import time
import os
import random
import datetime

BASE_URL = "https://1900.com.vn"
START_URL = "https://1900.com.vn/review-cong-ty"
OUTPUT_FILE = "data/reviews_1900_detailed.jsonl"
TARGET_REVIEWS_PER_COMPANY = 10
MAX_LIST_PAGES = 500  # Scan up to 500 list pages

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
}

def clean_text(text):
    return text.strip() if text else ""

def get_reviews_from_page(soup, company_url):
    reviews = []
    items = soup.select('.ReviewItem')
    for item in items:
        try:
            rating_tag = item.select_one('.ratingNumber')
            rating = clean_text(rating_tag.get_text()) if rating_tag else "N/A"
            
            title_tag = item.select_one('.ReviewTitle')
            title = clean_text(title_tag.get_text()) if title_tag else "N/A"
            
            meta_tag = item.select_one('.ReviewCandidateSubtext')
            meta_text = clean_text(meta_tag.get_text(" | ")) if meta_tag else ""
            
            pros = ""
            pros_label = item.select_one('strong.greenColor')
            if pros_label:
                pros_div = pros_label.find_next('div', class_='ReviewDetails')
                if pros_div:
                    content_div = pros_div.select_one('.expandable-content')
                    pros = clean_text(content_div.get_text("\n") if content_div else pros_div.get_text("\n"))

            cons = ""
            cons_label = item.select_one('strong.text-danger')
            if not cons_label:
                 for strong in item.select('strong'):
                     if "Nhược điểm" in strong.get_text():
                         cons_label = strong
                         break
            
            if cons_label:
                cons_div = cons_label.find_next('div', class_='ReviewDetails')
                if cons_div:
                    content_div = cons_div.select_one('.expandable-content')
                    cons = clean_text(content_div.get_text("\n") if content_div else cons_div.get_text("\n"))

            reviews.append({
                "title": title,
                "rating": rating,
                "meta": meta_text,
                "pros": pros,
                "cons": cons
            })
            
        except Exception as e:
            pass
            
    return reviews

def load_crawled_urls():
    if not os.path.exists(OUTPUT_FILE):
        return set()
    crawled = set()
    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                crawled.add(data.get('url'))
            except:
                pass
    return crawled

def crawl():
    # 1. Load existing
    crawled_urls = load_crawled_urls()
    print(f"Loaded {len(crawled_urls)} already crawled companies.")
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    print("Resuming crawl...")

    for page in range(1, MAX_LIST_PAGES + 1):
        list_url = f"{START_URL}?page={page}"
        print(f"Scanning list page {page}/{MAX_LIST_PAGES}: {list_url}")
        
        try:
            resp = requests.get(list_url, headers=headers, timeout=20)
            if resp.status_code != 200:
                print(f"  List page {page} returned status {resp.status_code}. Stopping.")
                break
                
            soup = BeautifulSoup(resp.text, 'html.parser')
            items = soup.select('.company-item')
            
            if not items:
                print("  No company items found on this page. Reached end of listing.")
                break
                
            for item in items:
                # --- LIST PAGE EXTRACTION ---
                link_tag = item.select_one('a.company-info')
                if not link_tag: 
                    continue
                    
                link = link_tag['href']
                if not link.startswith('http'):
                    link = BASE_URL + link
                    
                if link in crawled_urls:
                    continue
                
                # Company Name
                name_tag = item.select_one('.company-info p.font-weight-bold')
                company_name = clean_text(name_tag.get_text()) if name_tag else "Unknown"
                
                # Address (Location) from List Page
                address = ""
                # Heuristic: Address usually has .text-gray and Contains the Map Pin SVG
                # Map Pin SVG Path start: M21 10c0 7-9 13-9 13
                candidates = item.select('.company-info .text-gray')
                for cand in candidates:
                    txt = clean_text(cand.get_text())
                    html_str = str(cand)
                    
                    # Skip employee count
                    if "nhân viên" in txt:
                        continue
                        
                    # Check for Map Pin Path
                    if "M21 10c0 7-9 13-9 13" in html_str:
                        address = txt
                        break
                
                # If still empty, try looking for fa-map-marker or feather-map-pin in the whole item
                if not address:
                    for cand in candidates:
                         html_str = str(cand)
                         if 'map-marker' in html_str or 'map-pin' in html_str:
                             address = clean_text(cand.get_text())
                             break
                
                # Review Count from List Page
                review_count_total = 0
                
                # Review count is usually in the d-flex align-items-center line (Rating line)
                info_lines = item.select('.company-info .d-flex.align-items-center')
                for line in info_lines:
                     txt = clean_text(line.get_text())
                     if 'review' in txt.lower() or 'đánh giá' in txt.lower():
                        import re
                        m = re.search(r'(\d+(?:\.\d+)?)\s*([kmKM])?\s*(?:review|đánh giá)', txt, re.IGNORECASE)
                        if m:
                            try:
                                val = float(m.group(1))
                                mult = 1
                                suffix = m.group(2)
                                if suffix:
                                    if suffix.lower() == 'k': mult = 1000
                                    elif suffix.lower() == 'm': mult = 1000000
                                review_count_total = int(val * mult)
                            except:
                                pass
                
                # Fallback: if review count is 0
                if review_count_total == 0:
                     for line in info_lines:
                         html_str = str(line)
                         if 'comment' in html_str or 'message' in html_str:
                             txt = clean_text(line.get_text())
                             if len(txt) < 20 and any(c.isdigit() for c in txt):
                                 import re
                                 m = re.search(r'(\d+(?:\.\d+)?)', txt)
                                 if m:
                                     review_count_total = int(float(m.group(1)))

                print(f"  > {company_name} | Reviews: {review_count_total} | Loc: {address}")
                
                # --- DETAIL PAGE CRAWLING ---
                try:
                    # Append orderBy=DATE
                    join_char = '&' if '?' in link else '?'
                    # We start with page 1
                    detail_base_url = f"{link}{join_char}orderBy=DATE"
                    
                    collected_reviews = []
                    rating = ""
                    
                    # Loop to fetch reviews (pagination)
                    review_page = 1
                    while True:
                        if len(collected_reviews) >= TARGET_REVIEWS_PER_COMPANY:
                            break
                        if review_page > 1 and len(collected_reviews) >= review_count_total:
                             # If we supposedly fetched all available reviews
                             break
                        # Safety break for pages
                        if review_page > 10: 
                            break

                        curr_url = f"{detail_base_url}&page={review_page}"
                        # print(f"    Fetching reviews page {review_page}...")
                        
                        detail_resp = requests.get(curr_url, headers=headers, timeout=15)
                        if detail_resp.status_code != 200:
                            break
                            
                        dsoup = BeautifulSoup(detail_resp.text, 'html.parser')
                        
                        # Extract Details (only on first page mostly, but good to check)
                        if review_page == 1:
                            # 1. Rating
                            rating_span = dsoup.select_one('span.rating.font-weight-bold')
                            if rating_span:
                                rating = clean_text(rating_span.get_text().replace('★', ''))
                            
                            # 2. Address (Update if possible)
                            # Sometimes detail page has full address. 
                            # Usually in a box: .company-info -> .text-gray
                            # But often 1900 just shows the city like list page
                            pass
                        
                        # Extract Reviews
                        page_reviews = get_reviews_from_page(dsoup, link)
                        if not page_reviews:
                            break
                            
                        collected_reviews.extend(page_reviews)
                        
                        # If we found less reviews than "next page" logic usually implies, we might be done
                        # But 1900 pagination logic: check if there is a 'Next' button or just try next page
                        # If page_reviews is empty, we break above.
                        
                        review_page += 1
                        time.sleep(0.1)

                    # Truncate if needed (but user said "crawl AT LEAST 10", so more is fine. 
                    # "mỗi công ty phải cào ít nhất 10 lượt review"
                    # But also "nếu ít review < 10 thì phải cào tối đa".
                    # I will keep all I fetched up to reasonable limit (10 pages) to ensure I meet "at least 10". 
                    # If I have 15, that satisfies "at least 10".
                    
                    # Final Record
                    record = {
                        "company_name": company_name,
                        "address": address,
                        "rating": rating,
                        "review_count": review_count_total, # The total count displayed on site
                        "reviews": collected_reviews,
                        "source": "1900",
                        "url": link,
                        "crawled_at": datetime.datetime.now().isoformat()
                    }
                    
                    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(record, ensure_ascii=False) + "\n")
                    
                    crawled_urls.add(link)
                    
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"    Error crawling detail {link}: {e}")

        except Exception as e:
            print(f"Error fetching list page {page}: {e}")
            time.sleep(5)
            
    print("Crawl finished.")

if __name__ == "__main__":
    crawl()
