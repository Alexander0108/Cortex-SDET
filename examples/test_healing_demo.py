import asyncio
from playwright.async_api import async_playwright

async def test_login():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        try:
            await page.goto("https://the-internet.herokuapp.com/login")
            
            # Fill in the username field (corrected selector)
            username_field = page.locator("#username")
            await username_field.fill("tomsmith")
            
            # Fill in the password field
            password_field = page.locator("#password")
            await password_field.fill("SuperSecretPassword!")
            
            # Click the login button
            login_button = page.locator("button[type='submit']")
            await login_button.click()
            
            # Wait for the page to load after login
            await page.wait_for_load_state("networkidle")
            
            # Assert that the login was successful by checking for a flash message
            flash_message = page.locator("#flash-messages")
            assert "You logged into a secure area!" in await flash_message.inner_text()
            
        except Exception as e:
            await page.screenshot(path="failure_screenshot.png")
            raise e
        finally:
            await browser.close()

# Run the test
asyncio.run(test_login())