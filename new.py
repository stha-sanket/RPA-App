import time
import random
from playwright.sync_api import sync_playwright

url = "https://www.amazon.com/s?k=laptop&crid=1W5MH80IRZQ0O&sprefix=lapto%2Caps%2C348"

# --- Configuration ---
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0",
]

DELAY_RANGE = (2, 5)  # Delay in seconds between requests (randomized)

def scrape_amazon(url):
    with sync_playwright() as p:
        # Launch the browser
        browser = p.chromium.launch(headless=True)  # You can set headless=False for debugging purposes
        
        # Set user-agent while creating the context (not after creation)
        context = browser.new_context(
            user_agent=random.choice(USER_AGENTS)  # Set the user agent here
        )

        # Open a new page in the context
        page = context.new_page()

        # Navigate to the URL
        page.goto(url)

        # Wait for the page to load
        time.sleep(random.uniform(*DELAY_RANGE))

        # Find laptop elements (adjust the selector to match Amazon's page structure)
        laptop_elements = page.query_selector_all('div[data-component-type="s-search-result"]')

        for laptop in laptop_elements:
            try:
                name_element = laptop.query_selector('a.a-link-normal.s-underline-text.s-underline-link-text.s-link-style.a-text-normal')
                name = name_element.inner_text().strip() if name_element else "Name not found"

                # Price extraction
                price_whole_element = laptop.query_selector('span.a-price-whole')
                price_fraction_element = laptop.query_selector('span.a-price-fraction')

                if price_whole_element and price_fraction_element:
                    price = f"${price_whole_element.inner_text().strip()}.{price_fraction_element.inner_text().strip()}"
                else:
                    price = "Price not found"

                print(f"Name: {name}\nPrice: {price}\n---")

            except Exception as e:
                print(f"Error extracting data from laptop element: {e}")

        # Random delay between requests
        delay = random.uniform(*DELAY_RANGE)
        print(f"Sleeping for {delay:.2f} seconds...")
        time.sleep(delay)

        # Close the browser context and browser
        context.close()
        browser.close()

if __name__ == "__main__":
    scrape_amazon(url)
