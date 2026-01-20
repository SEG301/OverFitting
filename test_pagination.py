from curl_cffi import requests
from bs4 import BeautifulSoup

def test_pagination():
    url = "https://itviec.com/companies/fpt-software/review?page=2"
    print(f"Fetching {url}...")
    resp = requests.get(url, impersonate="chrome120", timeout=10)
    print(f"Status: {resp.status_code}")
    
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Check if we have review content different from page 1?
    # Or check if we have any reviews at all.
    reviews = soup.select('.content-of-review')
    print(f"Found {len(reviews)} reviews on page 2")
    
    if len(reviews) > 0:
        first_review = reviews[0]
        title = first_review.select_one('h3')
        if title:
            print(f"First review title on page 2: {title.get_text(strip=True)}")

if __name__ == "__main__":
    test_pagination()
