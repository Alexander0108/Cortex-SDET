# 🧠 Cortex-SDET: Autonomous AI-Powered Testing Framework
Cortex-SDET is a professional-grade QA Automation orchestrator that leverages Large Language Models (LLMs) to generate, execute, and self-heal E2E tests in real-time.

## 🌟 Strategic Advantages
- **Intent-Based Testing**: Describe business logic in plain English; the AI handles complex Playwright selectors.
- **Hybrid Brain**: Seamlessly switch between OpenAI (GPT-4o) for high-speed cloud execution and Ollama (DeepSeek-R1) for local data privacy.
- **Self-Healing Engine**: Automatically diagnoses failures and proposes code fixes based on real-time DOM analysis and stack traces.
- **Rich Visual Reporting**: Generates comprehensive HTML reports with timestamps, error logs, and failure screenshots.
- **Human-in-the-Loop (HITL)**: Prevents AI hallucinations by requiring engineer approval before applying self-healing code fixes.

## 🛠 Tech Stack
- **Core**: Python 3.9+
- **Driver**: Playwright (Async API)
- **Scraper**: Custom BeautifulSoup4 DOM Sanitizer
- **Intelligence**: OpenAI API & Local LLMs (Ollama)

## 🚀 Quick Start
Clone the repo:
```bash
git clone https://github.com/your-username/Cortex-SDET.git
cd Cortex-SDET
```

Local AI Setup (Optional but recommended):
Install Ollama and pull the required local model:
```bash
ollama pull deepseek-r1:8b
```

Environment Setup:
Install dependencies and Playwright browsers:
```bash
pip install -r requirements.txt
playwright install
```

Configure .env:
Create a .env file in the root directory and add your OpenAI key if using Cloud mode:
```env
OPENAI_API_KEY=your_actual_key_here
```

Run Orchestrator:
```bash
python3 main.py
```

## 🖼 Demonstration
### 1. Happy Path: Precision Execution
The agent successfully identifies stable selectors using custom DOM cleaning logic and executes the task flawlessly on the first attempt.
![Success Flow](images/success_flow.png)

### 2. Self-Healing: Automatic Recovery
When a test fails (e.g., due to a missing element or UI change), the system captures a failure screenshot, analyzes the error, and proposes a repaired script for engineer approval.
![Self-Healing Flow](images/healing_flow.png)

## 📊 How it Works
- **CortexScraper**: Captures and cleans the target website's HTML, removing "noise" to optimize LLM token usage.
- **CortexBridge**: Translates user tasks into executable Python code following strict SDET best practices.
- **CortexReporter**: Compiles execution data into professional HTML artifacts for stakeholders.

## 🛣 Future Roadmap
1. Integration with CI/CD pipelines (GitHub Actions).
2. Multi-page session persistence.
3. Visual Regression testing module.

*Developed by Oleksandr Dermanskij - Junior QA Automation Engineer*