import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

class CortexScraper:
    def __init__(self):
        # Added placeholder - great for TodoMVC!
        self.qa_attrs = ["id", "class", "data-qa", "data-testid", "name", "role", "type", "placeholder"]

    async def get_cleaned_html(self, url):
        async with async_playwright() as p:
            print(f"[*] Launching browser for: {url}")
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # 1. Navigate to page
            await page.goto(url, wait_until="commit") 
            
            # 2. Smart Wait
            try:
                # Wait for body to ensure DOM has started building
                await page.wait_for_selector("body", timeout=5000)
                # Wait for network idle as additional safeguard
                await page.wait_for_load_state("networkidle", timeout=5000)
            except Exception as e:
                print(f"[*] Warning while waiting for page: {e}")
                
            await asyncio.sleep(2) # Safety margin for heavy JS animations
            
            raw_html = await page.content()
            await browser.close()
            return self.clean_dom(raw_html)

    def clean_dom(self, html):
        soup = BeautifulSoup(html, "html.parser")
        
        # REMOVED "header" and "footer" from the blacklist
        for tag in soup(["script", "style", "svg", "path", "noscript", "link"]):
            tag.decompose()

        # Clean attributes of each tag
        for tag in soup.find_all(True):
            tag.attrs = {k: v for k, v in tag.attrs.items() if k in self.qa_attrs}
            
            # If tag is empty and has no attributes - we don't need it
            if not tag.contents and not tag.attrs:
                tag.decompose()

        return str(soup.prettify())

if __name__ == "__main__":
    scraper = CortexScraper()
    url = "https://demo.playwright.dev/todomvc/#/"
    
    cleaned = asyncio.run(scraper.get_cleaned_html(url))
    print("--- Cleaned HTML (first 500 characters) ---")
    print(cleaned[:500])