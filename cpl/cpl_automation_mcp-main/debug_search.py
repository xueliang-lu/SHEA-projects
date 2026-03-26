from playwright.sync_api import sync_playwright
from urllib.parse import quote_plus

def debug_search():
    query = "VU VIT1101 unit outline"
    search_url = f"https://duckduckgo.com/?q={quote_plus(query)}"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(search_url, wait_until="networkidle", timeout=30000)
        
        # Take a screenshot to see what's happening
        page.screenshot(path="debug_ddg.png")
        
        # Print some info
        print(f"Page title: {page.title()}")
        
        # Try a more generic selector
        links = page.locator("a")
        print(f"Total links found: {links.count()}")
        
        # Print text of first few links that look like results
        for i in range(min(50, links.count())):
            href = links.nth(i).get_attribute("href") or ""
            text = links.nth(i).inner_text().strip()
            if text and href.startswith("http") and "duckduckgo" not in href:
                print(f"Potential result: {text} -> {href}")
                
        browser.close()

if __name__ == "__main__":
    debug_search()
