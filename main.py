import asyncio, re, os, subprocess, sys, warnings
from datetime import datetime
from dotenv import load_dotenv
from scraper import CortexScraper
from bridge import CortexBridge
from reporter import CortexReporter

load_dotenv() # Load environment variables from .env

def clean_artifacts():
    files_to_delete = ["generated_test_result.py", "failure_screenshot.png"]
    for file in files_to_delete:
        if os.path.exists(file):
            os.remove(file)
            print(f"[*] Removed old artifact: {file}")

def extract_code(llm_output):
    # Remove extra whitespace/lines from start and end
    llm_output = llm_output.strip()
    # Search for python code blocks
    code_blocks = re.findall(r'```python\n(.*?)\n```', llm_output, re.DOTALL)
    if code_blocks:
        return code_blocks[0]

    # If no language-specific blocks found, search for any ``` blocks
    generic_blocks = re.findall(r'```\n(.*?)\n```', llm_output, re.DOTALL)
    if generic_blocks:
        return generic_blocks[0]

    return llm_output

def apply_test_fix(filepath, new_code):
    """
    Cleanly overwrites the test file content.
    Used in both interactive and batch mode.
    Returns the file path.
    """
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_code)
    print(f"\n{'='*50}")
    print("✨ AI FIX APPLIED  —  File patched automatically")
    print(f"📄 {os.path.basename(filepath)}")
    print(f"{'='*50}")
    return filepath

def extract_diagnosis(raw_response):
    """
    Extracts diagnosis from AI response (before code block).
    Returns the diagnosis string.
    """
    # First search in  thinking tags
    think_match = re.search(r' thinking(.*?) response', raw_response, re.DOTALL)
    if think_match:
        return think_match.group(1).strip()
    # Fallback: everything before ```python
    diagnosis = raw_response.split("```python")[0].strip()
    if diagnosis:
        return diagnosis
    # If nothing found
    return "Diagnosis not available."

def classify_error(error_msg):
    """
    Classifies error by Traceback text.
    
    - "selector" — NoSuchElementException, TimeoutError, locator issues
    - "assertion" — AssertionError (application bug)
    - "unknown" — everything else (attempt healing)
    """
    if not error_msg:
        return "unknown"
    
    error_lower = error_msg.lower()
    
    # Selector/timeout errors — heal
    if any(kw in error_lower for kw in [
        "nosuchelement", "timeouterror", "timeout", "locator",
        "page.wait_for", "element not found", "cannot locate",
        "strict mode violation", "multiple elements"
    ]):
        return "selector"
    
    # AssertionError — do not heal, this is an application bug
    if "assertionerror" in error_lower or "assert" in error_lower:
        return "assertion"
    
    # Default — attempt healing
    return "unknown"

def create_test_summary_md(base_name, url, task, model_name, status, report_path, error_msg=None, repair_details=None):
    """
    Creates .md test summary file in generated_tests/.
    If repair_details is provided — adds self-healing section.
    """
    md_file = os.path.join("generated_tests", f"test_{base_name}.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    error_section = ""
    if error_msg:
        # Truncate long errors to 500 characters
        truncated = error_msg[:500] + "..." if len(error_msg) > 500 else error_msg
        error_section = f"\n**❌ Errors:**\n```\n{truncated}\n```\n"

    repair_section = ""
    if repair_details:
        repair_section = f"""
## 🛠 Self-Healing Details

**🧠 Diagnosis:**
```
{repair_details.get('diagnosis', 'N/A')}
```

**📄 Changed File:** `generated_tests/test_{base_name}.py`
**🔧 Fix applied:** {repair_details.get('notes', 'Automated fix applied')}
"""

    content = f"""# 🧪 Test Summary: {base_name}

**📅 Date:** {timestamp}
**🤖 Model:** {model_name}
**🌐 URL:** [{url}]({url})
**📝 Task:** {task}
**✅ Status:** {status}
**📊 Report:** [{report_path}]({report_path})
{error_section}{repair_section}"""
    with open(md_file, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[📄] Test summary saved: {md_file}")
    return md_file

def check_smart_skip(base_name, req_file_path):
    """
    Smart Skip: checks if a generated .py file already exists,
    and if it's newer than the corresponding .txt file.
    Returns: 'run', 'regenerate', or None (if file doesn't exist).
    """
    py_file = os.path.join("generated_tests", f"test_{base_name}.py")

    if not os.path.exists(py_file):
        return None  # File doesn't exist, need to generate

    # Check modification dates
    py_mtime = os.path.getmtime(py_file)
    req_mtime = os.path.getmtime(req_file_path)

    if py_mtime >= req_mtime:
        # .py file is newer or same age
        print(f"\n[STEP] Test '{base_name}' already exists and is up-to-date.")
        print(f"   📄 .py: {datetime.fromtimestamp(py_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   📝 .txt: {datetime.fromtimestamp(req_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        choice = input("   👉 (1) Run existing / (2) Regenerate: ").strip()
        if choice == "2":
            return "regenerate"
        else:
            return "run"
    else:
        # .txt file is newer
        print(f"\n[STEP] Test '{base_name}' is stale (requirements updated).")
        print(f"   📄 .py: {datetime.fromtimestamp(py_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   📝 .txt: {datetime.fromtimestamp(req_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        choice = input("   👉 (1) Run existing / (2) Regenerate: ").strip()
        if choice == "2":
            return "regenerate"
        else:
            return "run"

async def execute_test(filepath):
    print(f"\n[STEP] Running test: {os.path.basename(filepath)}")
    try:
        # Important: timeout here (45s) must be larger than Playwright's timeout (30s)
        result = subprocess.run(
            ["python3", filepath],
            capture_output=True,
            text=True,
            timeout=45
        )

        print(f"   Return code: {result.returncode}")

        if result.returncode == 0:
            print("   ✅ TEST PASSED SUCCESSFULLY")
            return True, ""
        else:
            print("   ❌ TEST FAILED")
            return False, result.stderr

    except subprocess.TimeoutExpired:
        return False, "Process timed out after 45 seconds"
    except Exception as e:
        print(f"[!] Critical error while running test: {e}")
        return False, str(e)

async def run_agentic_qa(url, task, bridge):
    """
    INTERACTIVE MODE: with user confirmation (y/n).
    """
    clean_artifacts()
    scraper = CortexScraper()
    reporter = CortexReporter()

    cleaned_html = await scraper.get_cleaned_html(url)
    raw_code = bridge.generate_test(f"URL: {url}\nHTML: {cleaned_html}", task)
    generated_code = extract_code(raw_code)

    test_file = os.path.join(os.path.dirname(__file__), "generated_test_result.py")
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(generated_code)

    success, error_msg = await execute_test(test_file)

    # Determine status and screenshot
    screenshot_path = "failure_screenshot.png"
    status = "PASSED" if success else "FAILED"

    # Generate report
    reporter.generate_report(url, task, status, error_msg, screenshot_path)

    if not success:
        lang = getattr(bridge, "language", "en")  # for localized UI

        # Check screenshot before repair
        screenshot_path = os.path.join(os.path.dirname(__file__), "failure_screenshot.png")
        if os.path.exists(screenshot_path):
            print(f"{t(lang, 'sh_screenshot')} {screenshot_path}")

        print(t(lang, "sh_starting"))
        raw_repaired = bridge.repair_test(generated_code, error_msg, cleaned_html, task)
        repaired_code = extract_code(raw_repaired)

        print("\n" + "~"*50)
        print(t(lang, "sh_diagnosis"))
        print(extract_diagnosis(raw_repaired))
        print("~"*50)

        if "DIAGNOSTIC_FAIL" in raw_repaired:
            print("\n" + "!"*50)
            print(t(lang, "sh_critical"))
            print(f"Message: {raw_repaired.strip()}")
            print(t(lang, "sh_critical_explanation"))
            print("!"*50)
            return

        # Human-in-the-Loop: show a compact diff BEFORE applying
        print("\n" + "="*50)
        print(t(lang, "sh_diff_header"))
        print(t(lang, "sh_diff_legend"))
        print("-" * 50)
        print(code_diff_summary(generated_code, repaired_code))
        print("="*50)

        # INTERACTIVE MODE: ask for confirmation
        user_choice = input(t(lang, "sh_confirm")).lower()

        if user_choice == 'y':
            print(t(lang, "sh_applied"))
            apply_test_fix(test_file, repaired_code)

            print(t(lang, "sh_restarting"))
            success, error_msg = await execute_test(test_file)

            if success:
                print(t(lang, "sh_success"))
            else:
                print(t(lang, "sh_failed"))
                if error_msg:
                    print(f"{t(lang, 'sh_final_error')}\n{error_msg}")
        else:
            print(t(lang, "sh_cancelled"))


def parse_task_file(file_path, lang="en"):
    """
    Parses task file from requirements/.
    Searches for URL in text using regex.
    Returns (url, task_description).
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read().strip()

    # Search for URL in text (http:// or https://)
    url_match = re.search(r'https?://[^\s"\'<>]+', content)
    if url_match:
        url = url_match.group(0).rstrip('.,;:!?)')
    else:
        if lang == "uk":
            print(f"\n[!] У файлі {file_path} не знайдено посилання (URL).")
            print("    Файл буде пропущено.")
            print("    Додайте http/https посилання прямо в текст вимоги, наприклад:")
            print('    "Open https://site.com and login"')
        else:
            print(f"\n[!] No URL found in {file_path}.")
            print("    File skipped.")
            print("    Please include an http/https link inside the requirement text, e.g.:")
            print('    "Open https://site.com and login"')
        return None, None

    # Remove URL from text to get clean task description
    task = content.replace(url_match.group(0), "").strip()
    # Clean extra characters
    task = task.strip('",.;:!? ')
    if not task:
        task = content  # If nothing remains after URL removal, use the full text

    return url, task


async def generate_from_file(file_path, bridge):
    """
    Generates test from task file.
    BATCH MODE: self-healing without user confirmation.
    """
    print(f"\n[STEP] ===== Processing file: {os.path.basename(file_path)} =====")
    print(f"[READING] File: {file_path}")
    url, task = parse_task_file(file_path, getattr(bridge, "language", "en"))

    if not url or not task:
        print(f"[!] Skipping {file_path}: unable to parse URL or task.")
        return

    print(f"[READING] URL: {url}")
    print(f"[READING] Task: {task[:100]}..." if len(task) > 100 else f"[READING] Task: {task}")

    # Generate filename based on input file name
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_file = os.path.join("generated_tests", f"test_{base_name}.py")

    # Initialize reporter and scraper immediately (needed in all branches)
    reporter = CortexReporter()
    scraper = CortexScraper()

    # Smart Skip: check if test already exists
    skip_action = check_smart_skip(base_name, file_path)

    if skip_action == "run":
        # Run existing test without regeneration
        print(f"[STEP] Running existing test: {output_file}")
        success, error_msg = await execute_test(output_file)

        screenshot_path = "failure_screenshot.png"
        status = "PASSED" if success else "FAILED"
        repair_details = None

        if not success:
            # Analyze error
            error_type = classify_error(error_msg)
            print(f"\n🔍 Error type: {error_type}")

            if error_type == "assertion":
                # AssertionError — application bug, don't change code
                print("[!] AssertionError: logged as an application bug. Test code unchanged.")
                status = "FAILED (Assertion Bug)"
            elif error_type in ("selector", "unknown"):
                # Self-healing for existing test — Human-in-the-Loop
                lang = getattr(bridge, "language", "en")
                print(t(lang, "sh_starting"))
                try:
                    cleaned_html = await scraper.get_cleaned_html(url)
                    old_code = open(output_file, "r").read()
                    raw_repaired = bridge.repair_test(old_code, error_msg, cleaned_html, task)
                    repaired_code = extract_code(raw_repaired)
                    diagnosis = extract_diagnosis(raw_repaired)
                    print(f"\n{t(lang, 'sh_diagnosis')} {diagnosis[:200]}{'...' if len(diagnosis) > 200 else ''}")

                    if "DIAGNOSTIC_FAIL" not in raw_repaired:
                        # Show compact diff and ask for confirmation
                        print("\n" + "="*50)
                        print(t(lang, "sh_diff_header"))
                        print(t(lang, "sh_diff_legend"))
                        print("-" * 50)
                        print(code_diff_summary(old_code, repaired_code))
                        print("="*50)

                        user_choice = input(t(lang, "sh_confirm")).lower()

                        if user_choice == 'y':
                            print(t(lang, "sh_applied"))
                            old_snippet = old_code[:200]
                            apply_test_fix(output_file, repaired_code)

                            print(t(lang, "sh_restarting"))
                            success, error_msg = await execute_test(output_file)

                            if success:
                                print(t(lang, "sh_success"))
                                status = "FIXED BY AI"
                                repair_details = {
                                    'diagnosis': diagnosis,
                                    'notes': f"Self-healed existing test. Old snippet: {old_snippet[:100]}..."
                                }
                            else:
                                print(t(lang, "sh_failed"))
                                if error_msg:
                                    print(f"{t(lang, 'sh_final_error')}\n{error_msg}")
                        else:
                            print(t(lang, "sh_cancelled"))
                    else:
                        print(f"\n[!] AI could not fix: element missing from DOM.")
                        print(f"[!] Similar elements found: {raw_repaired}")
                except Exception as e:
                    print(f"[!] Error during self-healing: {e}")

        # Generate report
        report_path = reporter.generate_report(url, task, status, error_msg, screenshot_path)
        print(f"[📊] Report saved: {report_path}")

        create_test_summary_md(base_name, url, task, bridge.model_name, status, report_path, error_msg, repair_details)
        print(f"[✅] Done: {output_file}")
        return

    elif skip_action == "regenerate":
        print(f"[STEP] Regenerating test: {base_name}")
        # Continue with generation below

    # If skip_action is None or "regenerate" — generate new test
    print(f"[GENERATING] Requesting {bridge.model_name}...")

    cleaned_html = await scraper.get_cleaned_html(url)
    raw_code = bridge.generate_test(f"URL: {url}\nHTML: {cleaned_html}", task)
    generated_code = extract_code(raw_code)

    # Add comment with reference to requirements file at the start of code
    req_comment = f"# Generated from: {file_path}\n# Task: {task}\n# Model: {bridge.model_name}\n# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    generated_code = req_comment + generated_code

    print(f"[SAVING] Saving to {output_file}")
    os.makedirs("generated_tests", exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(generated_code)

    print(f"[EXECUTING] Running test: {output_file}")
    success, error_msg = await execute_test(output_file)

    # Determine status and screenshot
    screenshot_path = "failure_screenshot.png"
    status = "PASSED" if success else "FAILED"
    repair_details = None

    # Generate report
    report_path = reporter.generate_report(url, task, status, error_msg, screenshot_path)
    print(f"[📊] Report saved: {report_path}")

    if success:
        # Create .md summary for successful test
        create_test_summary_md(base_name, url, task, bridge.model_name, status, report_path)
    else:
        lang = getattr(bridge, "language", "en")  # for localized UI

        # Self-healing: attempt repair with user confirmation (Human-in-the-Loop)
        screenshot_full = os.path.join(os.path.dirname(__file__), "failure_screenshot.png")
        if os.path.exists(screenshot_full):
            print(f"{t(lang, 'sh_screenshot')} {screenshot_full}")

        print(t(lang, "sh_starting"))
        raw_repaired = bridge.repair_test(generated_code, error_msg, cleaned_html, task)
        repaired_code = extract_code(raw_repaired)

        # Extract diagnosis for report
        diagnosis = extract_diagnosis(raw_repaired)
        print(f"\n{t(lang, 'sh_diagnosis')} {diagnosis[:200]}{'...' if len(diagnosis) > 200 else ''}")

        if "DIAGNOSTIC_FAIL" in raw_repaired:
            print(f"\n[!] AI could not fix test: element missing from DOM.")
            print(f"[!] Similar elements found: {raw_repaired}")
            print(f"[!] Error file preserved: {output_file}")
            # Create .md summary with error
            create_test_summary_md(base_name, url, task, bridge.model_name, status, report_path, error_msg)
            return

        # Human-in-the-Loop: show compact diff and ask for confirmation
        print("\n" + "="*50)
        print(t(lang, "sh_diff_header"))
        print(t(lang, "sh_diff_legend"))
        print("-" * 50)
        print(code_diff_summary(generated_code, repaired_code))
        print("="*50)

        user_choice = input(t(lang, "sh_confirm")).lower()

        if user_choice != 'y':
            print(t(lang, "sh_cancelled"))
            create_test_summary_md(base_name, url, task, bridge.model_name, status, report_path, error_msg)
            return

        # Save old code for report (first 200 characters)
        old_code_snippet = generated_code[:200]

        # Apply fix
        print(t(lang, "sh_applied"))
        apply_test_fix(output_file, repaired_code)

        print(t(lang, "sh_restarting"))
        success, error_msg = await execute_test(output_file)

        if success:
            print(t(lang, "sh_success"))
            status = "PASSED (after self-heal)"
        else:
            print(t(lang, "sh_failed"))
            if error_msg:
                print(f"{t(lang, 'sh_final_error')}\n{error_msg}")

        # Collect repair details for .md report
        repair_details = {
            'diagnosis': diagnosis,
            'notes': f"Automated fix applied. Old code snippet: {old_code_snippet[:100]}..."
        }

        # Update report after repair
        reporter.generate_report(url, task, status, error_msg, screenshot_path)

        # Create .md summary with repair details
        create_test_summary_md(
            base_name, url, task, bridge.model_name, status, report_path,
            error_msg, repair_details
        )

    print(f"[✅] Done: {output_file}")


async def batch_process(bridge):
    """
    Batch mode: scans requirements/ and generates tests for each file.
    """
    print("\n" + "="*50)
    print("📦 BATCH TEST GENERATION MODE")
    print("="*50)

    req_dir = "requirements"
    if not os.path.exists(req_dir):
        print(f"[!] Directory '{req_dir}' not found. Creating...")
        os.makedirs(req_dir)

    files = [f for f in os.listdir(req_dir) if f.endswith(".txt")]
    if not files:
        print(f"[!] No .txt files found in '{req_dir}'")
        return

    print(f"[*] Files found: {len(files)}")
    for f in files:
        print(f"   - {f}")

    for file_name in files:
        file_path = os.path.join(req_dir, file_name)
        await generate_from_file(file_path, bridge)

    print("\n" + "="*50)
    print("✅ BATCH GENERATION COMPLETE")
    print("="*50)


# ══════════════════════════════════════════════════════════════════════════
# UNIFIED CONTROL CENTER — helpers for the master hub
# ══════════════════════════════════════════════════════════════════════════

def select_language():
    """
    Asks the user which language AI should use for natural-language answers.
    Technical terms, error codes and exceptions always stay in English.
    Returns: "en" or "uk"
    """
    print("\n┌─ AI RESPONSE LANGUAGE ─────────────────────────┐")
    print("│  1. 🇺🇦  Українська                              │")
    print("│      (AI відповідає українською; професійні     │")
    print("│       терміни, коди помилок та код — англійською)│")
    print("│                                                 │")
    print("│  2. 🇬🇧  English                                 │")
    print("│      (AI answers in English by default)         │")
    print("└─────────────────────────────────────────────────┘")

    while True:
        choice = input("\n👉 Select language (1 or 2): ").strip()
        if choice == "1":
            print("[✅] AI language set to: 🇺🇦 Українська")
            return "uk"
        elif choice == "2":
            print("[✅] AI language set to: 🇬🇧 English")
            return "en"
        print("⚠️  Invalid choice. Please enter 1 or 2.")


# ══════════════════════════════════════════════════════════════════════════
# BILINGUAL UI — all hub texts in Ukrainian and English
# ══════════════════════════════════════════════════════════════════════════

TRANSLATIONS = {
    "uk": {
        "welcome_title": "🧠  ВІТАЄМО У CORTEX-SDET ORCHESTRATOR",
        "welcome_subtitle": "    Єдиний центр керування: AI · API · SQL · DDT",
        "menu_ai": "🤖 AI-ТЕСТУВАННЯ",
        "opt1_title": "1. 💬 Інтерактивний генератор UI",
        "opt1_desc": "   └─ створює Playwright-тест за описом сайту + Self-Healing",
        "opt2_title": "2. 📦 Пакетний генератор тестів",
        "opt2_desc": "   └─ автоматично генерує та запускає тести з папки requirements/",
        "menu_suites": "🔌 ТЕСТОВІ МОДУЛІ",
        "opt3_title": "3. 🌐 REST API Тестування",
        "opt3_desc": "   └─ CRUD PetStore, JSON Schema та перевірка безпеки API",
        "opt3_short": "REST API Тестування",
        "opt4_title": "4. 📁 SQL БД та Формати даних",
        "opt4_desc": "   └─ запити SQLite (JOIN/GROUP BY) та валідація JSON/CSV/XML",
        "opt4_short": "SQL БД та Формати даних",
        "opt5_title": "5. 📊 Data-Driven Тестування",
        "opt5_desc": "   └─ валідація бізнес-правил користувачів і товарів з CSV/JSON",
        "opt5_short": "Data-Driven Тестування",
        "menu_allinone": "🚀 ВСЕ-В-ОДНОМУ ТА ЗВІТИ",
        "opt6_title": "6. ⚡ Запуск ПОВНОГО набору тестів",
        "opt6_desc": "   └─ миттєвий прогін усіх 67 тестів (API + SQL + Data-Driven)",
        "opt7_title": "7. 📑 Генерація єдиного Dashboard",
        "opt7_desc": "   └─ HTML-індекс усіх звітів, скріншотів та саммарі AI",
        "menu_info": "📖 ДОВІДКА",
        "opt8_title": "8. 💡 About / Quick Guide",
        "opt8_desc": "   └─ короткий огляд: що це, звідки дані, як працює",
        "opt0": "0. ❌ Вихід",
        "menu_prompt": "\n👉 Оберіть опцію: ",
        "invalid_choice": "⚠️  Некоректний вибір. Введіть 0-8.",
        "exit_msg": "\n👋 Вихід з Cortex-SDET. До побачення!",
        "enter_module": "🔌 ВХІД У МОДУЛЬ",
        "back_to_hub": "✅ ПОВЕРНЕННЯ В ХАБ — модуль",
        "launching": "[*] Запуск:",
        "module_not_found": "[❌] Модуль не знайдено:",
        "module_interrupted": "\n[⚠️] Модуль перервано користувачем. Повертаємось у хаб...",
        "module_exit_code": "[!] Модуль завершився з кодом",
        "select_option": "\n👉 Оберіть опцію: ",
        # Self-healing UI (Human-in-the-Loop)
        "sh_starting": "[🛠] ЗАПУСК РЕМОНТУ (SELF-HEALING)...",
        "sh_screenshot": "[📸] Скріншот помилки знайдено:",
        "sh_diagnosis": "🧠 ДІАГНОСТИКА AI:",
        "sh_diff_header": "🔄 ЗМІНИ, ЯКІ ПРОПОНУЄ AI:",
        "sh_diff_legend": "   (рядки з 🔴 — видалено, з 🟢 — додано; решта — контекст)",
        "sh_suggested": "✨ ПРОПОНОВАНИЙ КОД AI (повністю):",
        "sh_confirm": "✅ Застосувати це виправлення до файлу тесту? (y/n): ",
        "sh_applied": "✅ Виправлення застосовано. Тест оновлено.",
        "sh_restarting": "[*] Перезапуск виправленого тесту...",
        "sh_success": "[✨] SELF-HEALING УСПІШНИЙ! Тест пройдено після виправлення.",
        "sh_failed": "[💀] ❌ AI не зміг виправити цей тест.",
        "sh_final_error": "Фінальна помилка:",
        "sh_cancelled": "[⚠️] Виправлення скасовано користувачем. Файл не змінено.",
        "sh_critical": "🛑 AI-АГЕНТ ВИЯВИВ КРИТИЧНИЙ ЗБІЙ:",
        "sh_critical_explanation": "Пояснення: потрібний елемент відсутній у DOM. AI відмовився створювати хибний тест.",
    },

    "en": {
        "welcome_title": "🧠  WELCOME TO CORTEX-SDET ORCHESTRATOR",
        "welcome_subtitle": "    Unified Control Center: AI · API · SQL · DDT",
        "menu_ai": "🤖 AI AGENTIC TESTING",
        "opt1_title": "1. 💬 Interactive UI Generator",
        "opt1_desc": "   └─ build a Playwright test from URL + Self-Healing",
        "opt2_title": "2. 📦 Batch Test Generator",
        "opt2_desc": "   └─ auto-generate & run tests from requirements/",
        "menu_suites": "🔌 TESTING SUITES",
        "opt3_title": "3. 🌐 REST API Testing",
        "opt3_desc": "   └─ PetStore CRUD, JSON Schema & API security checks",
        "opt3_short": "REST API Testing",
        "opt4_title": "4. 📁 SQL DB & Data Formats",
        "opt4_desc": "   └─ SQLite queries (JOIN/GROUP BY) & JSON/CSV/XML validation",
        "opt4_short": "SQL DB & Data Formats",
        "opt5_title": "5. 📊 Data-Driven Testing",
        "opt5_desc": "   └─ business rule validation for users/products from CSV/JSON",
        "opt5_short": "Data-Driven Testing",
        "menu_allinone": "🚀 ALL-IN-ONE & REPORTING",
        "opt6_title": "6. ⚡ Run FULL Test Suite",
        "opt6_desc": "   └─ run all 67 tests at once (API + SQL + Data-Driven)",
        "opt7_title": "7. 📑 Generate Unified Dashboard",
        "opt7_desc": "   └─ HTML index of all reports, screenshots & AI summaries",
        "menu_info": "📖 INFO",
        "opt8_title": "8. 💡 About / Quick Guide",
        "opt8_desc": "   └─ quick overview: what it is, where data comes from, how it works",
        "opt0": "0. ❌ Exit",
        "menu_prompt": "\n👉 Select option: ",
        "invalid_choice": "⚠️  Invalid choice. Please enter 0-8.",
        "exit_msg": "\n👋 Exiting Cortex-SDET. Goodbye!",
        "enter_module": "🔌 ENTERING MODULE:",
        "back_to_hub": "✅ BACK TO HUB — module",
        "launching": "[*] Launching:",
        "module_not_found": "[❌] Module not found:",
        "module_interrupted": "\n[⚠️] Module interrupted by user. Returning to hub...",
        "module_exit_code": "[!] Module exited with code",
        "select_option": "\n👉 Select option: ",
        # Self-healing UI (Human-in-the-Loop)
        "sh_starting": "[🛠] STARTING SELF-HEALING REPAIR...",
        "sh_screenshot": "[📸] Error screenshot found:",
        "sh_diagnosis": "🧠 AI DIAGNOSIS:",
        "sh_diff_header": "🔄 CHANGES PROPOSED BY AI:",
        "sh_diff_legend": "   (🔴 = removed, 🟢 = added; other lines are context)",
        "sh_suggested": "✨ FULL SUGGESTED AI CODE:",
        "sh_confirm": "✅ Apply this fix to the test file? (y/n): ",
        "sh_applied": "✅ Fix applied. Test file updated.",
        "sh_restarting": "[*] Restarting fixed test...",
        "sh_success": "[✨] SELF-HEALING SUCCESSFUL! Test passed after the fix.",
        "sh_failed": "[💀] ❌ AI could not fix this test.",
        "sh_final_error": "Final error:",
        "sh_cancelled": "[⚠️] Repair cancelled by user. File left unchanged.",
        "sh_critical": "🛑 AI AGENT DETECTED A CRITICAL FAILURE:",
        "sh_critical_explanation": "Explanation: the requested element is missing from the DOM. AI refused to create a false test.",
    },
}


def t(lang, key):
    """Localized string lookup — falls back to English."""
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, TRANSLATIONS["en"].get(key, key))


def code_diff_summary(old_code, new_code, max_lines=18):
    """
    Builds a compact 'BEFORE → AFTER' diff between two code versions.
    Only changed lines are shown (unified diff). Returns a string.
    """
    import difflib
    old_lines = old_code.splitlines()
    new_lines = new_code.splitlines()
    diff = list(difflib.unified_diff(old_lines, new_lines, lineterm="", n=1))

    shown = 0
    out = []
    for line in diff[2:]:  # skip ---/+++ headers
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("@@"):
            out.append(f"   {line}")
            continue
        if line.startswith("+"):
            out.append(f"   🟢 {line[1:]}")
            shown += 1
        elif line.startswith("-"):
            out.append(f"   🔴 {line[1:]}")
            shown += 1
        else:
            out.append(f"      {line[1:]}")
        if shown >= max_lines:
            out.append(f"   ... (truncated, {len(diff)} diff lines total)")
            break

    if not out:
        return "   (no code changes detected)"
    return "\n".join(out)


def show_quick_guide(lang):
    """Prints a compact bilingual framework overview directly in the terminal."""
    if lang == "uk":
        rows = [
            "CORTEX-SDET - КОРОТКИЙ ГІД",
            "",
            "ЩО ЦЕ?",
            "Оркестратор тестування з AI-ядром: генерує, запускає та",
            "самостійно лікує Playwright-тести за текстовими описами.",
            "",
            "ГОТОВІ (pre-built) ТЕСТИ - вже написані в репозиторії:",
            "- API (пункт 3): api_tests/ - CRUD, JSON Schema, безпека",
            "- SQL (пункт 4): sql_tests/ - запити та формати (SQLite)",
            "- Data-Driven (пункт 5): data_driven_tests/ - валідація CSV/JSON",
            "  бізнес-правил: email/@, пароль >= 8, роль admin/user/editor,",
            "  ціна > 0, stock >= 0. [!] 6 негативних записів ПАДАЮТЬ навмисно!",
            "",
            "AI-ГЕНЕРОВАНІ ТЕСТИ - створюються на льоту (пункти 1-2):",
            "- Interactive (пункт 1): ви вводите URL + опис у терміналі,",
            "  AI пише тест і зберігає у generated_test_result.py",
            "- Batch (пункт 2): AI читає файли з requirements/ і генерує",
            "  окремий тест для кожного: generated_tests/test_<name>.py",
            "",
            "ФОРМАТ ФАЙЛІВ У requirements/ (важливо!):",
            "Текст вимоги ОБОВ'ЯЗКОВО має містити посилання http(s)://...",
            'Приклад: "Open https://site.com and login with test@mail.com"',
            "Без URL файл буде пропущено з помилкою.",
            "",
            "ЯК ПРАЦЮЄ SELF-HEALING?",
            "Тест впав -> система знімає HTML + скріншот -> AI аналізує помилку",
            "-> показує diff змін -> ви ПІДТВЕРДЖУЄТЕ виправлення -> перезапуск.",
            "",
            "ЗВІТИ: пункт 6 = прогін усіх 67 тестів, пункт 7 = HTML-дашборд.",
        ]
    else:
        rows = [
            "CORTEX-SDET - QUICK GUIDE",
            "",
            "WHAT IS IT?",
            "A testing orchestrator with an AI core: it generates, runs and",
            "self-heals Playwright tests from plain-text descriptions.",
            "",
            "PRE-BUILT TESTS - already written & stored in the repo:",
            "- API (option 3): api_tests/ - CRUD, JSON Schema, security",
            "- SQL (option 4): sql_tests/ - SQL queries & formats (SQLite)",
            "- Data-Driven (option 5): data_driven_tests/ - validates CSV/JSON",
            "  business rules: email/@, password >= 8, role admin/user/editor,",
            "  price > 0, stock >= 0. [!] 6 negative records FAIL by design!",
            "",
            "AI-GENERATED TESTS - created on the fly (options 1-2):",
            "- Interactive (option 1): you type URL + description in the terminal,",
            "  AI writes the test and saves it to generated_test_result.py",
            "- Batch (option 2): AI reads files from requirements/ and generates",
            "  a separate test per file: generated_tests/test_<name>.py",
            "",
            "FORMAT OF FILES IN requirements/ (important!):",
            "The requirement text MUST contain an http(s):// link.",
            'Example: "Open https://site.com and login with test@mail.com"',
            "Without a URL the file is skipped with an error.",
            "",
            "HOW DOES SELF-HEALING WORK?",
            "Test fails -> system grabs HTML + screenshot -> AI diagnoses",
            "-> shows a diff -> you CONFIRM the fix -> test re-runs.",
            "",
            "REPORTING: option 6 = run all 67 tests, option 7 = HTML dashboard.",
        ]

    TOTAL = 74
    print()
    print("┌" + "─" * (TOTAL - 2) + "┐")
    for row in rows:
        print(_render_line(row, TOTAL))
    print("└" + "─" * (TOTAL - 2) + "┘")
def run_module_cli(module_name, module_path, lang="en"):
    """
    Runs one of the sub-suite CLIs inside the main process.
    After the module exits, control returns to the hub menu.
    """
    print("\n" + "="*60)
    print(f"{t(lang, 'enter_module')} {module_name}")
    print("="*60)
    print(f"{t(lang, 'launching')} python3 {module_path}")
    try:
        result = subprocess.run([sys.executable, module_path], check=False)
        if result.returncode != 0:
            print(f"{t(lang, 'module_exit_code')} {result.returncode}")
    except FileNotFoundError:
        print(f"{t(lang, 'module_not_found')} {module_path}")
    except KeyboardInterrupt:
        print(t(lang, "module_interrupted"))
    print("\n" + "="*60)
    print(f"{t(lang, 'back_to_hub')} '{module_name}'")
    print("="*60)


async def interactive_mode(bridge):
    """
    Interactive mode: current logic with manual URL and prompt input.
    """
    print("\n" + "="*50)
    print("💬 INTERACTIVE MODE")
    print("="*50)

    target_url = input("\n🌐 Enter target URL (e.g. https://the-internet.herokuapp.com/login): ").strip()
    user_task = input("📝 Enter your test prompt (describe what the AI should test): ").strip()

    await run_agentic_qa(target_url, user_task, bridge)


def run_full_suite():
    """
    Runs ALL test modules (API + SQL + Data-Driven) in one shot via pytest.
    Negative test cases in data/ will fail by design (data validation demo).
    """
    print("\n" + "="*60)
    print("🚀 FULL TEST SUITE (API + SQL + DATA-DRIVEN)")
    print("="*60)
    print("[*] Running: pytest api_tests/ sql_tests/ data_driven_tests/ -v\n")

    start = datetime.now()
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "api_tests/", "sql_tests/",
         "data_driven_tests/", "-v"],
        capture_output=True,
        text=True
    )
    duration = (datetime.now() - start).total_seconds()

    print(result.stdout)
    if result.stderr:
        print(f"  stderr: {result.stderr[-500:]}")

    passed, failed = _parse_pytest_summary(result.stdout)
    total = passed + failed
    print("\n" + "="*60)
    if failed:
        print(f"❌ {failed}/{total} FAILED, {passed} PASSED "
              f"(time: {duration:.1f}s)")
        print("   💡 Note: failed cases in data_driven_tests/ are "
              "negative test data by design.")
    else:
        print(f"✅ ALL {total} TESTS PASSED (time: {duration:.1f}s)")
    print("="*60)
    return passed, failed, duration


def _parse_pytest_summary(stdout):
    """
    Parses the pytest 'x passed, y failed' summary line.
    Returns (passed, failed).
    """
    passed = failed = 0
    for line in stdout.splitlines():
        if " passed" in line and "failed" in line:
            passed_match = re.search(r'(\d+)\s+passed', line)
            failed_match = re.search(r'(\d+)\s+failed', line)
            passed = int(passed_match.group(1)) if passed_match else 0
            failed = int(failed_match.group(1)) if failed_match else 0
            break
        elif " passed" in line:
            match = re.search(r'(\d+)\s+passed', line)
            if match:
                passed = int(match.group(1))
            break
    return passed, failed



def generate_unified_dashboard():
    """
    Generates a single HTML dashboard that aggregates:
    - pytest HTML reports from reports/ (AI UI tests)
    - .md test summaries from generated_tests/ (batch AI tests)
    Returns the dashboard path.
    """
    reporter = CortexReporter()
    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
    generated_dir = os.path.join(os.path.dirname(__file__), "generated_tests")

    report_files = []
    if os.path.exists(reports_dir):
        report_files = sorted(
            [f for f in os.listdir(reports_dir) if f.endswith(".html")]
        )

    md_files = []
    if os.path.exists(generated_dir):
        md_files = sorted(
            [f for f in os.listdir(generated_dir) if f.endswith(".md")]
        )

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dashboard_path = os.path.join(reports_dir, "dashboard_index.html")

    report_items = "".join(
        f'<li class="list-group-item d-flex justify-content-between">'
        f'<a href="{f}" target="_blank">{f}</a>'
        f'<span class="badge bg-primary rounded-pill">report</span></li>'
        for f in report_files
    ) or '<li class="list-group-item text-muted">No reports yet — run AI UI tests first.</li>'

    md_items = "".join(
        f'<li class="list-group-item d-flex justify-content-between">'
        f'<a href="{f}" target="_blank">{f}</a>'
        f'<span class="badge bg-secondary rounded-pill">summary</span></li>'
        for f in md_files
    ) or '<li class="list-group-item text-muted">No summaries yet — run Batch AI mode first.</li>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Cortex-SDET Unified Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {{ background-color: #f8f9fa; padding: 40px; }}
        .card {{ border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); border: none; }}
        .stat {{ font-size: 2.2rem; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="mb-4">🧠 Cortex-SDET Unified Dashboard</h1>
        <p class="text-muted">Generated: {timestamp}</p>

        <div class="row g-3 mb-4">
            <div class="col-md-4">
                <div class="card text-center p-3">
                    <div class="text-muted">AI HTML Reports</div>
                    <div class="stat text-primary">{len(report_files)}</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-center p-3">
                    <div class="text-muted">AI Test Summaries</div>
                    <div class="stat text-secondary">{len(md_files)}</div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card text-center p-3">
                    <div class="text-muted">Test Modules</div>
                    <div class="stat text-success">4</div>
                </div>
            </div>
        </div>

        <div class="card p-4 mb-4">
            <h4>📊 AI UI Test Reports</h4>
            <ul class="list-group">{report_items}</ul>
        </div>

        <div class="card p-4">
            <h4>📝 AI Batch Test Summaries</h4>
            <ul class="list-group">{md_items}</ul>
        </div>
    </div>
</body>
</html>"""

    with open(dashboard_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\n[📊] UNIFIED DASHBOARD GENERATED: {dashboard_path}")
    return dashboard_path

def init_bridge(lang):
    """
    Interactively selects the AI provider and returns a configured CortexBridge.
    Used by hub options 1 (Interactive) and 2 (Batch).
    """
    print("\n┌─ AI PROVIDER ──────────────────────────────────┐")
    print("│  1. 💻  Local (Ollama — qwen2.5:3b)            │")
    print("│  2. ☁️   Cloud OpenAI (GPT-4o-mini)            │")
    print("│      🔑 Requires OPENAI_API_KEY in .env        │")
    print("│                                                │")
    print("│  3. ☁️   Cloud Google (gemini-3-flash)         │")
    print("│      🔑 Requires GEMINI_API_KEY in .env        │")
    print("│                                                │")
    print("│  4. ☁️   Cloud OpenRouter (DeepSeek V4) ⭐     │")
    print("│      🔑 Requires OPENROUTER_API_KEY in .env    │")
    print("└────────────────────────────────────────────────┘")

    provider_choice = input("\n👉 Select provider (1, 2, 3 or 4): ").strip()

    if provider_choice == "2":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("\n❌ ERROR: OPENAI_API_KEY not found in .env file")
            return None
        return CortexBridge(model_name="gpt-4o-mini", use_cloud=True, api_key=api_key, language=lang)

    elif provider_choice == "3":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("\n❌ ERROR: GEMINI_API_KEY not found in .env file")
            return None
        return CortexBridge(model_name="gemini-3-flash-preview", use_cloud=True, api_key=api_key, language=lang)

    elif provider_choice == "4":
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("\n❌ ERROR: OPENROUTER_API_KEY not found in .env file")
            return None
        return CortexBridge(
            model_name="deepseek/deepseek-chat",
            use_cloud=True,
            api_key=api_key,
            use_openrouter=True,
            language=lang
        )

    else:
        return CortexBridge(model_name="qwen2.5:3b", use_cloud=False, language=lang)


def _disp_width(s):
    """
    Estimates the on-screen display width of a string (wide CJK/emoji
    characters take 2 columns). Used to align the menu borders perfectly.
    """
    import unicodedata
    w = 0
    for ch in s:
        o = ord(ch)
        # Variation selector / ZWJ take no column space on their own
        if 0xFE00 <= o <= 0xFE0F or o == 0x200D:
            continue
        # Wide CJK + common emoji blocks (incl. ⚡ 0x26A1, ℹ 0x2139 with VS16)
        if (unicodedata.east_asian_width(ch) in ("W", "F")
                or 0x1F000 <= o <= 0x1FAFF
                or 0x2600 <= o <= 0x27BF
                or o == 0x2139):
            w += 2
        else:
            w += 1
    return w


def _render_line(text, total=74):
    """
    Renders one content line inside the box borders, with padding computed
    from the real display width (emoji/CJK = 2 columns). Guarantees a
    straight right edge regardless of font/terminal.
    """
    pad = total - _disp_width(text) - 4  # │ + space + space + │
    if pad < 0:
        pad = 0
    return "│ " + text + " " * pad + " │"


def print_hub_menu(lang="en"):
    """
    Prints the unified, localized main menu of the Control Center.
    Borders are rendered dynamically with per-line padding, so the
    right edge always forms one straight vertical line.
    """
    T = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    TOTAL = 74  # full width incl. border chars

    print()
    print("┌" + "─" * (TOTAL - 2) + "┐")
    print(_render_line(T["menu_ai"], TOTAL))
    print(_render_line(T["opt1_title"], TOTAL))
    print(_render_line(T["opt1_desc"], TOTAL))
    print(_render_line(T["opt2_title"], TOTAL))
    print(_render_line(T["opt2_desc"], TOTAL))
    print(_render_line("", TOTAL))
    print(_render_line(T["menu_suites"], TOTAL))
    print(_render_line(T["opt3_title"], TOTAL))
    print(_render_line(T["opt3_desc"], TOTAL))
    print(_render_line(T["opt4_title"], TOTAL))
    print(_render_line(T["opt4_desc"], TOTAL))
    print(_render_line(T["opt5_title"], TOTAL))
    print(_render_line(T["opt5_desc"], TOTAL))
    print(_render_line("", TOTAL))
    print(_render_line(T["menu_allinone"], TOTAL))
    print(_render_line(T["opt6_title"], TOTAL))
    print(_render_line(T["opt6_desc"], TOTAL))
    print(_render_line(T["opt7_title"], TOTAL))
    print(_render_line(T["opt7_desc"], TOTAL))
    print(_render_line("", TOTAL))
    print(_render_line(T["menu_info"], TOTAL))
    print(_render_line(T["opt8_title"], TOTAL))
    print(_render_line(T["opt8_desc"], TOTAL))
    print(_render_line("", TOTAL))
    print(_render_line(T["opt0"], TOTAL))
    print("└" + "─" * (TOTAL - 2) + "┘")


def main():
    """Main entry point — unified Control Center (bilingual UI)."""
    # ─── Step 1: Language selection for the whole UI + AI ───────
    lang = select_language()
    print("\n" + "="*60)
    print(t(lang, "welcome_title"))
    print(t(lang, "welcome_subtitle"))
    print("="*60)

    # ─── Step 2: Main hub loop ──────────────────────────────────
    while True:
        print_hub_menu(lang)
        choice = input(t(lang, "menu_prompt")).strip()

        if choice == "1":
            # AI Agentic Interactive mode
            bridge = init_bridge(lang)
            if bridge:
                asyncio.run(interactive_mode(bridge))

        elif choice == "2":
            # Batch generation mode
            bridge = init_bridge(lang)
            if bridge:
                asyncio.run(batch_process(bridge))

        elif choice == "3":
            run_module_cli(t(lang, "opt3_short"), "api_tests/api_cli.py", lang)

        elif choice == "4":
            run_module_cli(t(lang, "opt4_short"), "sql_tests/sql_cli.py", lang)

        elif choice == "5":
            run_module_cli(t(lang, "opt5_short"), "data_driven_tests/data_cli.py", lang)

        elif choice == "6":
            run_full_suite()

        elif choice == "7":
            generate_unified_dashboard()

        elif choice == "8":
            show_quick_guide(lang)

        elif choice == "0":
            print(t(lang, "exit_msg"))
            break

        else:
            print(t(lang, "invalid_choice"))


if __name__ == "__main__":
    main()