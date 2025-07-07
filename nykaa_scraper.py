from playwright.sync_api import sync_playwright

def get_top_5_titles(keyword):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Go to Nykaa homepage
        page.goto("https://www.nykaafashion.com", timeout=60000)
        page.wait_for_timeout(3000)

        # Search for product
        page.fill("input[placeholder*='Search for products']", keyword)
        page.keyboard.press("Enter")

        # Wait for product cards
        page.wait_for_selector("div.product-card-wrap", timeout=30000)
        page.wait_for_timeout(2000)
        page.mouse.wheel(0, 2000)

        # Get product cards
        cards = page.query_selector_all("div.product-card-wrap")
        titles = []

        for card in cards[:5]:
            try:
                brand = card.query_selector("div.css-bpa8nm")
                name = card.query_selector("div.css-1vufxwr")
                if brand and name:
                    titles.append(f"{brand.inner_text().strip()} - {name.inner_text().strip()}")
            except:
                continue

        # Write to file
        with open("top_titles.txt", "w", encoding="utf-8") as f:
            for title in titles:
                f.write(title + "\n")

        print("✅ Saved top 5 titles to top_titles.txt")
        browser.close()

get_top_5_titles("white shirt")
