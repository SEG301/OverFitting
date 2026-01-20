import time
import json
import undetected_chromedriver as uc
import os

def harvest_cookies(url="https://hsctvn.com"):
    print(f"Opening browser to harvest cookies from {url}...")
    
    options = uc.ChromeOptions()
    # options.add_argument('--headless') # Do not use headless for harvesting to be safe
    
    # Browser matching (same as ultimate crawler)
    browser_path = None
    possible_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
    ]
    for path in possible_paths:
        if os.path.exists(path):
            browser_path = path
            break
            
    if browser_path:
        options.binary_location = browser_path

    try:
        driver = uc.Chrome(options=options, browser_executable_path=browser_path, version_main=141)
    except:
        # Fallback
        options = uc.ChromeOptions()
        if browser_path: options.binary_location = browser_path
        driver = uc.Chrome(options=options, browser_executable_path=browser_path)

    try:
        driver.get(url)
        print("Please resolve any Captcha/Cloudflare manually if needed...")
        time.sleep(15) # Wait for manual interaction or auto-pass
        
        cookies = driver.get_cookies() or []
        print(f"Captured {len(cookies)} cookies.")
        print(f"Page Title: {driver.title}")
        # Dump homepage first
        with open("hsctvn_home.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        
        # Navigate to Ha Noi listing
        target = "https://hsctvn.com/ha-noi" 
        print(f"Navigating to: {target}")
        driver.get(target)
        time.sleep(10)
        with open("hsctvn_hanoi_dump.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        print("Dumped listings to hsctvn_hanoi_dump.html")
        
        with open("cookies.json", "w") as f:
            json.dump(cookies, f)
            
        print("Cookies saved to cookies.json")
        
        # Also save user agent
        ua = driver.execute_script("return navigator.userAgent;")
        with open("user_agent.txt", "w") as f:
            f.write(ua)
            
    finally:
        driver.quit()

if __name__ == "__main__":
    harvest_cookies()
