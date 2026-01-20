from curl_cffi import requests
from bs4 import BeautifulSoup

def test_itviec():
    # Trying Company Listing
    url = "https://itviec.com/companies"
    try:
        print(f"Fetching {url}...")
        resp = requests.get(url, impersonate="chrome120", timeout=10)
        print(f"Status: {resp.status_code}")
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Check for review section
        # ITviec usually has a review tab or section.
        # Let's see if we can find text "Reviews" and if the content is visible.
        
        page_text = soup.get_text()
        if "Sign in to view" in page_text or "Đăng nhập để xem" in page_text:
            print("Login wall detected in text.")
        else:
            print("No obvious login wall text found.")
            
        # Let's save the html to inspect manually just in case
        with open("debug_itviec_company.html", "w") as f:
            f.write(resp.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_itviec()
