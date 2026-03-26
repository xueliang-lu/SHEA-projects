from playwright.sync_api import sync_playwright
from urllib.parse import quote_plus

def test_fixed_search():
    query = "VU VIT1101 unit outline"
    search_url = f"https://duckduckgo.com/?q={quote_plus(query)}"
    
    with sync_playwright() as p:
        # Use a real user agent
        ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=ua)
        page = context.new_page()
        
        print(f"Searching for: {query}")
        page.goto(search_url, wait_until="networkidle")
        
        # Try different selectors
        selectors = [
            "a[data-testid='result-title-a']", # New DDG
            "h2 a", # Generic
            ".result__a", # Old DDG
        ]
        
        for sel in selectors:
            anchors = page.locator(sel)
            count = anchors.count()
            print(f"Selector '{sel}' found {count} results")
            if count > 0:
                for i in range(min(3, count)):
                    print(f"  - {anchors.nth(i).inner_text()} -> {anchors.nth(i).get_attribute('href')}")
        
        browser.close()

if __name__ == "__main__":
    test_fixed_search()
