# Generated from: requirements/login_test.txt
# Task: As a user, I want to open "", enter "tomsmith" in the "usernme" field and "SuperSecretPassword!" in the password field, and password field, and check if I see the welcome message "You logged into a secure area
# Model: deepseek/deepseek-chat
# Date: 2026-05-08 15:02:45

import asyncio
from playwright.async_api import async_playwright

async def test_login():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        try:
            await page.goto("https://the-internet.herokuapp.com/login")
            
            # Fill in the username field
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
            
            # Check if the welcome message is visible
            welcome_message = page.locator("#flash")
            assert "You logged into a secure area" in await welcome_message.inner_text()
            
        except Exception as e:
            await page.screenshot(path="failure_screenshot.png")
            raise e
        finally:
            await browser.close()

# Run the test
asyncio.run(test_login())