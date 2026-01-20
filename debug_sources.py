import asyncio
from curl_cffi.requests import AsyncSession

async def debug_fetch():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    async with AsyncSession(impersonate="chrome110", headers=headers) as s:
        # Debug Hosocongty
        print("Fetching Hosocongty...")
        try:
            r1 = await s.get("https://hosocongty.vn/ha-noi-tp1/page-1")
            print(f"Hosocongty Status: {r1.status_code}")
            with open("debug_hosocongty.html", "w", encoding="utf-8") as f:
                f.write(r1.text)
        except Exception as e:
            print(f"Hosocongty Error: {e}")

        # Debug Reviewcongty
        print("Fetching Reviewcongty...")
        try:
            r2 = await s.get("https://reviewcongty.com/companies?page=1")
            print(f"Reviewcongty Status: {r2.status_code}")
            with open("debug_reviewcongty.html", "w", encoding="utf-8") as f:
                f.write(r2.text)
        except Exception as e:
            print(f"Reviewcongty Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_fetch())
