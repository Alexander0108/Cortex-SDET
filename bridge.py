import time

class CortexBridge:
    def __init__(self, model_name="deepseek-r1:8b", use_cloud=False, api_key=None):
        self.model_name = model_name
        self.use_cloud = use_cloud
        
        # Initialize clients depending on the selected provider
        if self.use_cloud and api_key:
            if "gemini" in self.model_name.lower():
                # Initialize the Google Gemini-specific client
                try:
                    from google import genai  # type: ignore # New library for Gemini 2.0
                except Exception as e:
                    raise ImportError(
                        "Missing dependency for Gemini. Install it with: pip install google-genai"
                    ) from e

                self.gemini_client = genai.Client(api_key=api_key)
            else:
                # Standard OpenAI client (for GPT or DeepSeek Cloud)
                try:
                    from openai import OpenAI  # type: ignore
                except Exception as e:
                    raise ImportError(
                        "Missing dependency for OpenAI. Install it with: pip install openai"
                    ) from e

                self.client = OpenAI(api_key=api_key)

        self.system_prompt = """
            You are a Senior SDET (Software Development Engineer in Test).
            Your task is to write clean Playwright Python tests.

            STRICT RULES:
            1. LANGUAGE: Use ONLY Python with 'playwright.async_api'.
            2. NO SELENIUM: Using Selenium is a critical failure.
            3. NO CHAT in generation mode. BUT in REPAIR MODE, provide a brief 'DIAGNOSIS' strictly in UKRAINIAN before the code block.
            4. LINEAR LOGIC: Do NOT use internal if-statements to "handle" missing elements.
            5. VISUALS & ERROR HANDLING: Wrap the ENTIRE test logic (after browser launch) in a global 'try-except' block. 
                Inside the 'except' block: 
                1. FIRST take 'failure_screenshot.png' using 'await page.screenshot(full_page=True)'.
                2. THEN print the error.
                3. FINALLY raise the error so the orchestrator sees the failure.
                In the 'finally' block: Always call 'await browser.close()'.
            7. BEST PRACTICES: Use 'page.locator()' instead of 'page.query_selector()'.
            8. ASYNC RULES: Never 'await' the page.locator() method. Only 'await' actions like .click(), .fill().
            9. FORBIDDEN: NEVER use local 'try-except' inside the test for specific elements. If an element is missing, let the test crash.
            10. ANTI-HALLUCINATION: If the requested element is COMPLETELY missing from the HTML context, DO NOT generate code. Output ONLY: "DIAGNOSTIC_FAIL: Element missing".
            11. WAIT FOR ELEMENTS: Do NOT use hardcoded page.wait_for_timeout(). Rely on Playwright's auto-waiting.
            12. BROWSER: Always launch browser with 'headless=False' for visual debugging.
            13. INPUT SUBMISSION: When filling forms, if there is no explicit 'Submit' button, use 'await page.keyboard.press("Enter")'. 
            CRITICAL: After pressing "Enter", always add 'await page.wait_for_load_state("networkidle")' or a short 'await asyncio.sleep(1)' to ensure the action is processed.
            16. ELEMENT SEARCH STRATEGY: Look for standard semantic HTML tags (<input>, <button>, <a>) and generic attributes (name, placeholder, aria-label) instead of site-specific classes.
            17. PYTHON SYNTAX: Use snake_case. NEVER use 'textContent'. Use 'inner_text()' or 'text_content()'.
            18. SELECTORS: Use 'page.get_by_label', 'page.get_by_placeholder', or 'page.locator' with clear attributes from HTML.
            19. ASSERTIONS: Always check if an element is visible or contains text before finishing. Example: assert "Success" in await page.locator("#flash").inner_text().
            20. BOILERPLATE TEMPLATE: Always use this structure:
                async def test():
                    async with async_playwright() as p:
                        browser = await p.chromium.launch(headless=False)
                        page = await browser.new_page()
                        try:
                            # logic here
                        except Exception as e:
                            await page.screenshot(path="failure_screenshot.png")
                            raise e
                        finally:
                            await browser.close()
        """

    def _call_llm(self, prompt):
        """Internal method for routing requests (Gemini/OpenAI cloud or local)."""
        if self.use_cloud:
            # GOOGLE GEMINI LOGIC
            if "gemini" in self.model_name.lower():
                # Retry loop to handle quota limits (quota management)
                for attempt in range(3):
                    try:
                        response = self.gemini_client.models.generate_content(
                            model=self.model_name,
                            contents=[self.system_prompt, prompt]
                        )
                        # Strip potential Markdown fences from the response
                        return response.text.replace("```python", "").replace("```", "").strip()
                    except Exception as e:
                        error_str = str(e)
                        # Check for quota exhaustion (429) OR server overload (503)
                        if ("429" in error_str or "503" in error_str) and attempt < 2:
                            wait_time = 40  # seconds
                            print(f"[!] Сервер Google перевантажений або ліміт вичерпано. Пауза {wait_time}с... (Спроба {attempt + 1}/3)")
                            time.sleep(wait_time)
                        else:
                            # If the error is not quota-related or retries are exhausted, re-raise
                            raise e
            
            # OPENAI / DEEPSEEK CLOUD LOGIC
            else:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1
                )
                return response.choices[0].message.content
        else:
            # LOCAL OLLAMA LOGIC
            try:
                import ollama  # type: ignore
            except Exception as e:
                raise ImportError(
                    "Missing dependency for local Ollama. Install it with: pip install ollama"
                ) from e

            response = ollama.generate(
                model=self.model_name,
                system=self.system_prompt,
                prompt=prompt,
                options={"temperature": 0.1, "num_ctx": 4096}
            )
            return response['response']

    def generate_test(self, html_context, user_task):
        prompt = f"HTML Context:\n{html_context}\n\nTask: {user_task}"
        prefix = "☁️ [CLOUD]" if self.use_cloud else "💻 [LOCAL]"
        print(f"[*] {prefix} Запит до {self.model_name}...")
        return self._call_llm(prompt)
    
    def repair_test(self, original_code, error_message, current_html, user_task):
        prompt = f"""
            REPAIR MODE: Попередній тест впав. 
            ОРИГІНАЛЬНИЙ КОД: {original_code}
            ПОМИЛКА: {error_message}
            
            ЗАВДАННЯ:
            1. Напиши 'DIAGNOSIS' українською мовою: що саме пішло не так?
            2. Надай виправлений код.
            3. Використовуй тільки ті елементи, які є в HTML нижче.
            4. Враховуй попередні правила синтаксису (ніяких textContent).
            
            HTML КОНТЕКСТ:
            {current_html}
        """
        prefix = "☁️ [CLOUD]" if self.use_cloud else "💻 [LOCAL]"
        print(f"[*] {prefix} Запит на самовідновлення до {self.model_name}...")
        return self._call_llm(prompt)