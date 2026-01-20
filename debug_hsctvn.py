import asyncio
import json
from curl_cffi.requests import AsyncSession

async def check_hsctvn():
    # Load cookies
    try:
        with open("cookies.json", 'r') as f:
            cookies_list = json.load(f)
            cookies = {}
            for c in cookies_list:
                cookies[c['name']] = c['value']
    except:
        print("No cookies found")
        return

    # Load UA
    try:
        with open("user_agent.txt", 'r') as f:
            ua = f.read().strip()
    except:
        ua = "Mozilla/5.0"

    print(f"Testing with {len(cookies)} cookies...")
    
    async with AsyncSession(impersonate="chrome110", cookies=cookies, headers={"User-Agent": ua}) as s:
        # Try a listing page URL, assuming standard structure or just home
        # Usually it is /ha-noi/trang-1 or similar
        url = "https://hsctvn.com/ha-noi"
        print(f"Fetching {url}...")
        r = await s.get(url)
        print(f"Status: {r.status_code}")
        
        # Check for key content
        if "Mã số thuế" in r.text or "Danh sách doanh nghiệp" in r.text:
             print("SUCCESS: Found listing data!")
             # Preview
             print(r.text[:500])
             # Check for listing items
             print(f"Listing count estimate: {r.text.count('class=' + chr(34) + 'item' + chr(34))}")
        else:
             print("FAILED: Content still hidden/blocked.")
             print(r.text[:1000])

if __name__ == "__main__":
    asyncio.run(check_hsctvn())
