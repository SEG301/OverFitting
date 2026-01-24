import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

def analyze_list_page():
    url = "https://1900.com.vn/review-cong-ty"
    print(f"Fetching {url}...")
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    company_items = soup.select('.company-item')
    print(f"Found {len(company_items)} company items.")
    
    if company_items:
        first = company_items[0]
        # print html of first item to see structure
        print("First item HTML:")
        print(first.prettify())

def analyze_detail_page():
    # Use a known valid company link
    url = "https://1900.com.vn/danh-gia-dn/cong-ty-tnhh-mot-thanh-vien-isofhcare-12782" 
    # Or find one from list page to be fresh
    
    print(f"Fetching {url}...")
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Analyze Header for Address, Rating, Review Count
    print("\n--- Detail Page Analysis ---")
    
    # Address
    # Looking for address in the header
    # Hints: usually inside some info block
    print("Searching for address candidates:")
    # Dump text of likely containers
    containers = soup.select('div.company-info')
    for c in containers:
        print(c.get_text(strip=True)[:200])
        
    # Rating
    rating_span = soup.select_one('span.rating')
    if rating_span:
        print(f"Found rating span: {rating_span.get_text(strip=True)}")
    else:
        print("Rating span NOT found")
        
    # Review Count
    # Usually text like "X đánh giá"
    body_text = soup.get_text()
    if "đánh giá" in body_text:
        print("Found 'đánh giá' text in body.")
        
    # Reviews
    reviews = soup.select('.ReviewItem')
    print(f"Found {len(reviews)} reviews.")
    if reviews:
        r = reviews[0]
        print("First review HTML:")
        print(r.prettify())

if __name__ == "__main__":
    analyze_list_page()
    analyze_detail_page()
