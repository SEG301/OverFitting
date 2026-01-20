import os
import json
import time
import random
from bs4 import BeautifulSoup
from curl_cffi import requests
from urllib.parse import unquote, unquote_plus

OUTPUT_FILE = "data/reviews_itviec.jsonl"
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

class ITviecCrawler:
    def __init__(self):
        self.base_url = "https://itviec.com"
        self.session = requests.Session()
    
    def fetch(self, url):
        retries = 3
        for i in range(retries):
            try:
                print(f"Fetching {url}... (Attempt {i+1}/{retries})")
                resp = self.session.get(url, impersonate="chrome120", timeout=20)
                if resp.status_code == 200:
                    return resp.text
                elif resp.status_code == 404:
                    print(f"404 Not Found: {url}")
                    return None
                else:
                    print(f"Status {resp.status_code} for {url}. Retrying...")
                    time.sleep(2 * (i + 1))
            except Exception as e:
                print(f"Error fetching {url}: {e}. Retrying...")
                time.sleep(2 * (i + 1))
        return None

    def load_crawled_urls(self):
        crawled = set()
        if os.path.exists(OUTPUT_FILE):
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if 'url' in data:
                            crawled.add(data['url'])
                    except:
                        pass
        return crawled

    def crawl_all(self):
        self.crawled_urls = self.load_crawled_urls()
        print(f"Loaded {len(self.crawled_urls)} already crawled URLs (unique reviews, but we track companies by checking if we have ANY review for them? No, we check if we have visited the company page. Actually, multiple reviews share the same URL: company_review_url. So we can just check if ANY review from that url exists.)")
        
        # We need a set of company URLs, not individual review URLs (which are identical for a company usually, or we store the company review page url).
        # stored 'url' field is "https://itviec.com/companies/mb-bank/review".
        # So yes, we can track completed companies.
        
        page = 1
        while True:
            url = f"{self.base_url}/companies?page={page}"
            html = self.fetch(url)
            if not html:
                break
            
            soup = BeautifulSoup(html, 'html.parser')
            company_links = soup.select('a.featured-company')
            
            if not company_links:
                print(f"No companies found on page {page}. Stopping.")
                break
            
            print(f"Found {len(company_links)} companies on page {page}.")
            
            for link in company_links:
                review_path = link.get('href') # e.g. /companies/slug/review
                if not review_path:
                    continue
                
                # Check review count
                review_count_tag = link.select_one('.company__footer-reviews')
                review_count = 0
                if review_count_tag:
                    text = review_count_tag.get_text(strip=True)
                    # "124 reviews" -> 124
                    try:
                        review_count = int(text.split()[0])
                    except:
                        pass
                
                if review_count > 0:
                    # Construct full review URL first to check if already crawled
                    full_review_url = f"{self.base_url}{review_path}"
                    
                    if full_review_url in self.crawled_urls:
                        print(f"Skipping {full_review_url} (already crawled)")
                        continue

                    # Construct Overview URL from Review URL (remove '/review')
                    # review_path is like /companies/slug/review
                    overview_path = review_path.replace('/review', '')
                    overview_url = f"{self.base_url}{overview_path}"
                    
                    print(f"Fetching overview: {overview_url}")
                    detailed_addresses = self.get_company_details(overview_url)
                    
                    print(f"Crawling {review_count} reviews for {full_review_url}...")
                    self.crawl_company_reviews(full_review_url, detailed_addresses)
                else:
                    print(f"Skipping {review_path} (0 reviews)")
            
            page += 1
            time.sleep(random.uniform(1, 3))

    def get_company_details(self, overview_url):
        addresses = []
        try:
            html = self.fetch(overview_url)
            if html:
                soup = BeautifulSoup(html, 'html.parser')
                # Look for .location divs with data-location attribute
                location_divs = soup.select('.location[data-location]')
                for div in location_divs:
                    raw_loc = div.get('data-location')
                    if raw_loc:
                        decoded_loc = unquote_plus(raw_loc)
                        if decoded_loc not in addresses:
                            addresses.append(decoded_loc)
        except Exception as e:
            print(f"Error fetching/parsing details for {overview_url}: {e}")
        
        return addresses

    def crawl_company_reviews(self, company_review_url, detailed_addresses=[]):
        page = 1
        company_address = None
        total_collected = 0
        
        full_address_str = " | ".join(detailed_addresses) if detailed_addresses else None

        while True:
            if total_collected >= 10:
                break

            # Handle pagination
            if page == 1:
                url = company_review_url
            else:
                url = f"{company_review_url}?page={page}"
            
            html = self.fetch(url)
            if not html:
                break
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract company address on the first page (or every page if available)
            if not company_address:
                # Look for the map-pin icon and adjacent text
                # We iterate over all SVG uses to find the map-pin
                for use_tag in soup.select('svg use'):
                    if '#map-pin' in use_tag.get('href', ''):
                        # The parent svg, its parent span, next sibling div usually holds the address
                        # Structure: 
                        # <div> <span> <svg>...</svg> </span> <div class="small-text">Address</div> </div>
                        svg = use_tag.find_parent('svg')
                        if svg:
                            icon_container = svg.parent
                            if icon_container and icon_container.name == 'span':
                                address_div = icon_container.find_next_sibling('div')
                                if address_div:
                                    company_address = address_div.get_text(strip=True)
                                    break
            
            # Use specific selectors based on analysis
            # Try .content-of-review as primary, but also check .reviews-list-container items
            review_items = soup.select('.content-of-review')
            
            # If empty, maybe check valid alternate selector?
            if not review_items:
                # Fallback: select direct children of container?
                # Based on debug html, some reviews are just div.py-4 inside reviews-list-container
                # But let's rely on content-of-review first as it appeared in my grep.
                # Actually, in debug_itviec_company.html, lines 2603+, the first review (line 2609) is NOT in .content-of-review.
                # It is directly under .reviews-list-container -> div.py-4
                # BUT the SECOND review (line 5619) IS in .content-of-review.
                # This suggests simpler selector: .reviews-list-container .py-4.border-bottom-dashed
                container = soup.select_one('.reviews-list-container')
                if container:
                    review_items = container.select('.py-4.border-bottom-dashed')
            
            if not review_items:
                print(f"No reviews found on page {page} for {company_review_url}.")
                break
                
            print(f"  Found {len(review_items)} reviews on page {page}. Address: {full_address_str or company_address}")
            
            reviews_data = []
            for item in review_items:
                if total_collected >= 10:
                    break
                    
                review = self.parse_review(item, company_review_url)
                if review:
                    # Use detailed address if available, else fallback to scraped header address
                    if full_address_str:
                        review['company_address'] = full_address_str
                    else:
                        review['company_address'] = company_address
                    reviews_data.append(review)
                    total_collected += 1
            
            if not reviews_data:
                print(f"  Failed to parse any reviews on page {page}.")
                break
                
            # Save immediately
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                for review in reviews_data:
                    f.write(json.dumps(review, ensure_ascii=False) + "\n")
            
            if total_collected >= 10:
                print(f"  Reached limit of 10 reviews for {company_review_url}.")
                break

            # Stop if we found fewer items than typically on a full page (usually 10 or 20)
            # But let's just rely on getting 0 items next time for safety, 
            # Or if Next button is missing?
            # Safer to just increment page until 0 items found.
            page += 1
            time.sleep(random.uniform(0.5, 1.5))

    def parse_review(self, item, url):
        try:
            full_text = item.get_text(strip=True)
            if not full_text: return None
            
            # Title
            title_tag = item.select_one('h3')
            title = title_tag.get_text(strip=True) if title_tag else "No Title"
            
            # Date
            date_tag = item.select_one('.text-dark-grey.fw-400') # "August 2025" or similar
            date = date_tag.get_text(strip=True) if date_tag else ""
            
            # Rating
            # Look for number near stars
            # We observed <p class='ims-3 ime-1'>4</p>
            # Or assume structure: .d-flex.align-items-center > p (that contains number)
            rating = 0
            rating_p = item.select_one('.stars p.ims-3') # Attempt specific class
            if not rating_p:
                # Try finding any digit in star container
                star_container = item.select_one('.stars')
                if star_container:
                    text = star_container.get_text(strip=True)
                    # Extract first digit?
                    # text could be "4" or ""
                    try:
                        rating = int(text)
                    except:
                        pass
            else:
                try:
                    rating = int(rating_p.get_text(strip=True))
                except:
                    pass
            
            # Details: Pros/Cons
            # .what-you-liked .panel-paragraph
            # .feedback .panel-paragraph
            liked = ""
            liked_tag = item.select_one('.what-you-liked .panel-paragraph')
            if liked_tag:
                liked = liked_tag.get_text(strip=True)
                
            improvements = ""
            imp_tag = item.select_one('.feedback .panel-paragraph')
            if imp_tag:
                improvements = imp_tag.get_text(strip=True)
            
            # Recommend
            recommend = False
            if item.select_one('.recommend-icon-wrapper'):
                recommend = True
            
            return {
                "source": "Itviec",
                "url": url,
                "title": title,
                "date": date,
                "rating": rating,
                "liked": liked,
                "improvements": improvements,
                "recommend": recommend
            }
        except Exception as e:
            # print(f"Error parsing review: {e}")
            return None

if __name__ == "__main__":
    crawler = ITviecCrawler()
    crawler.crawl_all()
