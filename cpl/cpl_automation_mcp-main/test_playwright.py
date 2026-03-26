from playwright.sync_api import sync_playwright

def test():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            print("Chromium launched successfully")
            browser.close()
    except Exception as e:
        print(f"Failed to launch Chromium: {e}")

if __name__ == "__main__":
    test()
