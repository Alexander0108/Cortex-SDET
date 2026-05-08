import asyncio, re, os, subprocess, warnings
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
        # Check screenshot before repair
        screenshot_path = os.path.join(os.path.dirname(__file__), "failure_screenshot.png")
        if os.path.exists(screenshot_path):
            print(f"[📸] Error screenshot found: {screenshot_path}")

        print("[🛠] STARTING REPAIR...")
        raw_repaired = bridge.repair_test(generated_code, error_msg, cleaned_html, task)
        repaired_code = extract_code(raw_repaired)

        print("\n" + "~"*50)
        print("🧠 AI DIAGNOSIS:")
        print(extract_diagnosis(raw_repaired))
        print("~"*50)

        if "DIAGNOSTIC_FAIL" in raw_repaired:
            print("\n" + "!"*50)
            print("🛑 AI AGENT DETECTED A CRITICAL FAILURE:")
            print(f"Message: {raw_repaired.strip()}")
            print("Explanation: The requested element is missing from the DOM tree. AI refused to create a false test.")
            print("!"*50)
            return

        # Show code for review
        print("\n" + "="*50)
        print("✨ AI SUGGESTED FIX:")
        print("-" * 50)
        print(repaired_code)
        print("-" * 50)

        # INTERACTIVE MODE: ask for confirmation
        user_choice = input("✅ Apply this fix? (y/n): ").lower()

        if user_choice == 'y':
            apply_test_fix(test_file, repaired_code)

            print("[*] Restarting fixed test...")
            success, error_msg = await execute_test(test_file)

            if success:
                print("[✨] ✨ SELF-HEALING SUCCESSFUL!")
            else:
                print("[💀] ❌ AI could not fix this.")
                if error_msg:
                    print(f"Final error:\n{error_msg}")
        else:
            print("[⚠️] Repair cancelled by user. Exiting.")


def parse_task_file(file_path):
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
        print(f"[!] No URL found in {file_path}")
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
    url, task = parse_task_file(file_path)

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
                # Self-healing for existing test
                print("[🛠] STARTING SELF-HEALING FOR EXISTING TEST...")
                try:
                    cleaned_html = await scraper.get_cleaned_html(url)
                    raw_repaired = bridge.repair_test(
                        open(output_file, "r").read(), error_msg, cleaned_html, task
                    )
                    repaired_code = extract_code(raw_repaired)
                    diagnosis = extract_diagnosis(raw_repaired)
                    print(f"\n🧠 Diagnosis: {diagnosis[:200]}{'...' if len(diagnosis) > 200 else ''}")

                    if "DIAGNOSTIC_FAIL" not in raw_repaired:
                        print("[🛠] Applying automated fix...")
                        old_snippet = open(output_file, "r").read()[:200]
                        apply_test_fix(output_file, repaired_code)

                        print("[EXECUTING] Restarting fixed test...")
                        success, error_msg = await execute_test(output_file)

                        if success:
                            print("[✨] ✨ SELF-HEALING SUCCESSFUL!")
                            status = "FIXED BY AI"
                            repair_details = {
                                'diagnosis': diagnosis,
                                'notes': f"Self-healed existing test. Old snippet: {old_snippet[:100]}..."
                            }
                        else:
                            print("[💀] ❌ AI could not fix this.")
                            if error_msg:
                                print(f"Final error:\n{error_msg}")
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
        # Self-healing: attempt automatic repair
        screenshot_full = os.path.join(os.path.dirname(__file__), "failure_screenshot.png")
        if os.path.exists(screenshot_full):
            print(f"[📸] Error screenshot found: {screenshot_full}")

        print("[🛠] STARTING REPAIR (BATCH MODE)...")
        raw_repaired = bridge.repair_test(generated_code, error_msg, cleaned_html, task)
        repaired_code = extract_code(raw_repaired)

        # Extract diagnosis for report
        diagnosis = extract_diagnosis(raw_repaired)
        print(f"\n🧠 Diagnosis: {diagnosis[:200]}{'...' if len(diagnosis) > 200 else ''}")

        if "DIAGNOSTIC_FAIL" in raw_repaired:
            print(f"\n[!] AI could not fix test: element missing from DOM.")
            print(f"[!] Similar elements found: {raw_repaired}")
            print(f"[!] Error file preserved: {output_file}")
            # Create .md summary with error
            create_test_summary_md(base_name, url, task, bridge.model_name, status, report_path, error_msg)
            return

        # BATCH MODE: automatic fix application WITHOUT confirmation
        print("[🛠] Applying automated fix...")

        # Save old code for report (first 200 characters)
        old_code_snippet = generated_code[:200]

        # Apply fix
        apply_test_fix(output_file, repaired_code)

        print("[EXECUTING] Restarting fixed test...")
        success, error_msg = await execute_test(output_file)

        if success:
            print("[✨] ✨ SELF-HEALING SUCCESSFUL!")
            status = "PASSED (after self-heal)"
        else:
            print("[💀] ❌ AI could not fix this.")
            if error_msg:
                print(f"Final error:\n{error_msg}")

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


if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧠  WELCOME TO CORTEX-SDET ORCHESTRATOR")
    print("="*60)

    # ─── Block 1: Mode Selection ──────────────────────────────────
    print("\n┌─ MODE SELECTION ───────────────────────────┐")
    print("│  1. 💬  Interactive                         │")
    print("│      (manual URL and prompt input)          │")
    print("│                                              │")
    print("│  2. 📦  Batch                                │")
    print("│      (automatic generation from requirements/)│")
    print("└──────────────────────────────────────────────┘")

    mode_choice = input("\n👉 Select mode (1 or 2): ").strip()

    # ─── Block 2: AI Provider Selection ───────────────────────────
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

    # Provider selection logic and Bridge initialization
    bridge = None

    if provider_choice == "2":
        # OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("\n❌ ERROR: OPENAI_API_KEY not found in .env file")
            exit(1)
        bridge = CortexBridge(model_name="gpt-4o-mini", use_cloud=True, api_key=api_key)

    elif provider_choice == "3":
        # Google Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("\n❌ ERROR: GEMINI_API_KEY not found in .env file")
            exit(1)
        bridge = CortexBridge(model_name="gemini-3-flash-preview", use_cloud=True, api_key=api_key)

    elif provider_choice == "4":
        # OpenRouter (DeepSeek)
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("\n❌ ERROR: OPENROUTER_API_KEY not found in .env file")
            exit(1)
        bridge = CortexBridge(
            model_name="deepseek/deepseek-chat",
            use_cloud=True,
            api_key=api_key,
            use_openrouter=True
        )

    else:
        # Local mode by default or choice '1'
        bridge = CortexBridge(model_name="qwen2.5:3b", use_cloud=False)

    if mode_choice == "2":
        asyncio.run(batch_process(bridge))
    else:
        asyncio.run(interactive_mode(bridge))