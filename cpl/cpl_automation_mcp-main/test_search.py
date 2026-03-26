from playwright.sync_api import sync_playwright
from urllib.parse import quote_plus

def test_search():
    query = "VU VIT1101 unit outline"
    search_url = f"https://duckduckgo.com/?q={quote_plus(query)}"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000) # Wait for results to load
        
        # Check if results are there
        anchors = page.locator("a[data-testid='result-title-a']")
        count = anchors.count()
        print(f"Found {count} results")
        
        for i in range(min(5, count)):
            a = anchors.nth(i)
            print(f"Result {i+1}: {a.inner_text()} -> {a.get_attribute('href')}")
            
        browser.close()

if __name__ == "__main__":
    test_search()
