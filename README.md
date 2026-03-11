# Agentic-Slot: Autonomous AI Testing Framework 🚀

Professional-grade QA Automation tool that uses Local LLMs to generate, execute, and repair E2E tests.

## 🌟 Key Features
- **Reliable Execution**: High success rate on standard E2E scenarios. If the UI is stable, the agent executes tasks flawlessly without any human intervention.
- **Human-in-the-Loop Control**: Strategic verification step that allows engineers to approve or reject AI-proposed fixes before execution, ensuring 100% predictability.
- **Zero-Code Testing**: Describe your task in English (e.g., "Add task 'Buy Bitcoin'"), and the agent does the rest.
- **Self-Healing Logic**: If a test fails due to UI changes, the agent analyzes the Error Traceback + DOM and repairs the code automatically.
- **Enterprise Guardrails**: Strictly enforced Playwright best practices, preventing "False Positive" results.
- **Local & Private**: Powered by Ollama (Qwen2.5-Coder), ensuring no data leaves your machine.
- **Automated Artifacts**: Generates full-page screenshots on failure for rapid debugging.

## 🛠 Tech Stack
- **Language**: Python 3.9+
- **Automation**: Playwright (Async)
- **AI Brain**: Ollama (Qwen2.5-Coder:7b)
- **Parsing**: BeautifulSoup4 & Regex Sanitization

## 🚀 Quick Start
0. Install [Ollama](https://ollama.ai/) and pull the model: ollama pull qwen2.5-coder:7b
1. Install requirements: `pip install -r requirements.txt`
2. Install Playwright browsers: `playwright install`
3. Run the orchestrator: `python3 main.py`

## 📊 How it Works
1. **Scraper**: Extracts and cleans the target website's HTML.
2. **Bridge**: Sends HTML + User Task to the LLM.
3. **Execution**: Runs the generated script in an isolated subprocess.
4. **Healing**: If execution fails, the agent initiates a repair cycle based on the error log.

## 🖼 Demonstration

### 1. Happy Path: Precision Execution
The agent identifies the best selectors (using `data-testid`) and executes the task flawlessly on the first attempt.
![Success Flow](images/scenario1_success.png)

### 2. Dynamic Self-Healing & Human-in-the-Loop
When a direct instruction (like "Click the ADD button") is impossible, the agent analyzes the DOM, finds an alternative (like `press('Enter')`), and waits for engineer approval.
![Self-Healing Flow](images/scenario2_repair.png)

### 3. Anti-Hallucination & Boundary Recognition
If an element is truly missing from the DOM, the agent triggers the `DIAGNOSTIC_FAIL` guardrail instead of generating fake code.
![Boundary Diagnostic](images/scenario3_diagnostic.png)

### 4. Visual Evidence (Failure Artifacts)
Every failure generates a `failure_screenshot.png`, allowing for instant visual debugging of the AI's environment.
![UI Error State](images/ui_error_state.png)

## 📊 Future Roadmap
1. **Integration** with Jenkins/GitHub Actions.
2. **Support** for multi-modal models (Vision) for UI comparison.
3. **Compliance Testing**: Automated verification of regulatory requirements for iGaming transactions.
4. **Database validation** for iGaming transaction testing.

---
*Developed by Oleksandr Dermanskij - Junior QA Automation Engineer*