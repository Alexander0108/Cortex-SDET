# 🧠 Cortex-SDET: Autonomous AI-Powered Testing Framework

Cortex-SDET is a professional-grade QA Automation orchestrator that leverages Large Language Models (LLMs) to generate, execute, and self-heal E2E tests in real-time.

## 🌟 Strategic Advantages & ROI

- **Intent-Based Testing**: Describe business logic in plain language; the AI engine dynamically resolves complex Playwright selectors, reducing test maintenance time.
- **Resilience-First Architecture**: Integrated retry logic with exponential backoff gracefully handles Cloud API rate limits (HTTP 429) and server overloads (HTTP 503).
- **Hybrid Brain**: Seamless switching between OpenAI (GPT-4o), Google (Gemini 3 Flash), and Local LLMs (Qwen 2.5) balances execution speed with strict data privacy requirements.
- **Self-Healing Engine**: Automatically intercepts failures, diagnoses DOM state changes, and proposes code fixes (Human-in-the-Loop verified) to drastically cut down debugging hours.
- **Actionable Reporting**: Generates Bootstrap-based HTML artifacts embedding execution logs, diagnostic insights, and failure screenshots for stakeholder visibility.

## 🛠 Tech Stack

- **Core**: Python 3.9+, AsyncIO
- **Browser Automation**: Playwright (Async API)
- **DOM Processing**: Custom BeautifulSoup4 Sanitizer (Optimizes LLM token consumption)
- **Intelligence**: Google GenAI SDK, OpenAI API, Ollama (Local Models)

## 📊 Demonstration & Provider Benchmarks

| Provider                    | Status    | Highlighted Capability                                                              |
| :-------------------------- | :-------- | :---------------------------------------------------------------------------------- |
| **OpenAI (GPT-4o-mini)**    | ✅ Passed | **High-Speed Precision:** Optimal for complex logic generation with lowest latency. |
| **Google (Gemini 3 Flash)** | ✅ Passed | **Fault Tolerance:** Demonstrated auto-recovery during API 503 unavailability.      |
| **Local (Qwen 2.5:3b)**     | ✅ Passed | **Zero-Cost Privacy:** 100% offline execution optimized for Apple Silicon (M2).     |

### 1. Execution Flows (Multi-Provider Support)

**Standard Cloud Execution (OpenAI):**
![GPT Flow](images/success_flow_GPT.png)

**Resilience in Action (Gemini API Retry):**
The orchestrator detects server overload and successfully applies retry logic without test failure.
![Gemini Retry Flow](images/success_flow_gemini.png)

**Secure Local Execution (Ollama):**
Running completely offline, ensuring proprietary test data never leaves the machine.
![Local Execution](images/success_flow_Ollama_qwen.png)

### 2. Self-Healing Flow (The "Killer Feature")

When a locator changes or an element is missing, Cortex-SDET intercepts the crash, analyzes the error, and prompts the engineer with a repaired code snippet.
![Self-Healing Mechanism](images/self_healing_flow.png)

### 3. Diagnostic HTML Reporting

Each execution produces a clean, stakeholder-ready report. In case of failure, it provides clear diagnostic context (e.g., "Element missing") rather than raw stack traces.
![HTML Report Preview](images/report_preview.png)

## 🚀 Quick Start Guide

### Local Environment Setup

Install dependencies and Playwright browser binaries:
`pip install -r requirements.txt`
`playwright install`

### Provider SDKs (installed on demand)

The orchestrator supports multiple LLM providers. Their Python SDKs are only required when you actually use that provider.
They are already included in `requirements.txt`, so if you ran `pip install -r requirements.txt`, you typically don't need to install these separately:

- **OpenAI Cloud**: `pip install openai`
- **Google Gemini Cloud**: `pip install google-genai`
- **Local Ollama**: `pip install ollama`

Create a `.env` file in the root directory:
`OPENAI_API_KEY=your_openai_key`
`GEMINI_API_KEY=your_gemini_key`

### Local LLM Setup (Optional)

Install Ollama and pull the recommended lightweight model:
`ollama pull qwen2.5:3b`

### Run Orchestrator

`python3 main.py`

## 🧠 Core Architecture

- **CortexScraper**: Cleans raw HTML, stripping scripts and CSS to provide LLMs with a structured, token-efficient DOM tree.
- **CortexBridge**: The brain that translates intent into executable Playwright Python code.
- **CortexReporter**: Aggregates test metadata and constructs HTML artifacts.

## 🧩 Repo notes

- **Editor settings**: `.vscode/` is ignored via `.gitignore` (IDE-specific local settings).

_Designed and engineered by Oleksandr Dermanskij - AQA Engineer & AI Automation Specialist_
