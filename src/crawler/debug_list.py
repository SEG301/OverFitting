import requests
from bs4 import BeautifulSoup

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

def analyze_list_item():
    url = "https://1900.com.vn/review-cong-ty"
    print(f"Fetching {url}...")
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    company_items = soup.select('.company-item')
    print(f"Found {len(company_items)} company items.")
    
    if company_items:
        first = company_items[0]
        print("--- FIRST ITEM HTML ---")
        print(first.prettify())
        print("-----------------------")
        
        print("Trying selectors:")
        lines = first.select('.company-info .d-flex.align-items-center')
        print(f"Found {len(lines)} lines with '.company-info .d-flex.align-items-center'")
        for i, line in enumerate(lines):
            print(f"Line {i}: {line.get_text(strip=True)[:50]}")
            print(f"Line {i} classes: {line.get('class')}")
            svgs = line.select('svg')
            print(f"Line {i} SVGs: {len(svgs)}")
            for svg in svgs:
                print(f"   SVG classes: {svg.get('class')}")

if __name__ == "__main__":
    analyze_list_item()
