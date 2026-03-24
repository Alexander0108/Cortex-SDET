import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

class CortexScraper:
    def __init__(self):
        # placeholder додано - це супер для TodoMVC!
        self.qa_attrs = ["id", "class", "data-qa", "data-testid", "name", "role", "type", "placeholder"]

    async def get_cleaned_html(self, url):
        async with async_playwright() as p:
            print(f"[*] Запуск браузера для: {url}")
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            # 1. Заходимо на сторінку
            await page.goto(url, wait_until="commit") 
            
            # 2. Розумне очікування (Smart Wait)
            try:
                # Чекаємо появи хоча б body, щоб гарантувати, що DOM почав будуватися
                await page.wait_for_selector("body", timeout=5000)
                # Чекаємо мережевого спокою (Network Idle) як додаткову страховку
                await page.wait_for_load_state("networkidle", timeout=5000)
            except Exception as e:
                print(f"[*] Попередження під час очікування сторінки: {e}")
                
            await asyncio.sleep(2) # Захисний інтервал для важких JS-анімацій
            
            raw_html = await page.content()
            await browser.close()
            return self.clean_dom(raw_html)

    def clean_dom(self, html):
        soup = BeautifulSoup(html, "html.parser")
        
        # ВИДАЛЕНО "header" та "footer" з чорного списку
        for tag in soup(["script", "style", "svg", "path", "noscript", "link"]):
            tag.decompose()

        # Очищаємо атрибути кожного тегу
        for tag in soup.find_all(True):
            tag.attrs = {k: v for k, v in tag.attrs.items() if k in self.qa_attrs}
            
            # Якщо тег порожній і без атрибутів - він нам не треба
            if not tag.contents and not tag.attrs:
                tag.decompose()

        return str(soup.prettify())

if __name__ == "__main__":
    scraper = CortexScraper()
    url = "https://demo.playwright.dev/todomvc/#/"
    
    cleaned = asyncio.run(scraper.get_cleaned_html(url))
    print("--- Очищений HTML (перші 500 символів) ---")
    print(cleaned[:500])