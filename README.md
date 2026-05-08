# 🧠 Cortex-SDET Orchestrator

**Autonomous AI-Powered E2E Testing Framework**

Cortex-SDET is a professional-grade QA Automation orchestrator that leverages Large Language Models (LLMs) to generate, execute, and self-heal end-to-end Playwright tests in real-time. It transforms natural-language test descriptions into executable code, dramatically reducing test maintenance costs and eliminating flaky tests.

---

## 📈 Value Proposition & ROI

| Problem                                                       | Cortex-SDET Solution                                                                            | Impact                                          |
| ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| **Flaky tests** consume 40%+ of QA engineering time           | Autonomous self-healing engine detects DOM changes and patches selectors automatically          | ~80% reduction in test maintenance              |
| **Test creation** requires deep Playwright/Selenium expertise | Intent-based testing: describe business logic in plain language                                 | Non-technical stakeholders can contribute tests |
| **Multi-environment** complexity (local vs cloud)             | Hybrid Brain seamlessly switches between Local (Ollama), OpenAI, Google Gemini, and DeepSeek V4 | Zero-config provider switching                  |
| **API rate limits** & server overloads                        | Integrated retry logic with exponential backoff (HTTP 429/503)                                  | Resilient CI/CD pipelines                       |
| **Debugging overhead**                                        | Bootstrap-based HTML reports with failure screenshots, DOM snapshots, and AI diagnosis          | Stakeholder-ready visibility                    |

---

## ✨ Key Features

### 🤖 Multi-LLM Support

Choose your intelligence layer based on speed, cost, and privacy requirements:

| Provider           | Model          | Best For                                          |
| ------------------ | -------------- | ------------------------------------------------- |
| **OpenAI**         | GPT-4o-mini    | High-speed precision, complex logic generation    |
| **Google**         | Gemini 3 Flash | Fault tolerance, auto-recovery under load         |
| **OpenRouter**     | DeepSeek V4 ⭐ | Best price/performance ratio for batch generation |
| **Local (Ollama)** | Qwen 2.5:3b    | Zero-cost privacy, 100% offline on Apple Silicon  |

### 🧠 Smart Error Classification

The system intelligently classifies test failures:

- **Selector Errors** (`NoSuchElementException`, `TimeoutError`): Full self-healing cycle — DOM analysis → AI repair → code patch → retry
- **Assertion Errors** (`AssertionError`): Logged as application bugs. Test code is **never** modified — the bug is in the app, not the test
- **Unknown Errors**: Best-effort repair attempt with full diagnostic output

### 🛠 Self-Healing Engine

When a locator changes or an element goes missing:

1. **Intercept**: Catch the crash with full Traceback
2. **Diagnose**: AI analyzes the DOM state and error message
3. **Suggest alternatives**: If the exact element is missing, the AI finds 2-3 similar interactive elements (other inputs, buttons, etc.)
4. **Patch**: Automatically rewrite the test file with corrected selectors
5. **Retry**: Re-execute the fixed test
6. **Report**: Generate a detailed report with `"FIXED BY AI"` status

### 📦 Batch Mode

Process multiple test requirements in a single run:

1. Place `.txt` files in `requirements/` with natural-language descriptions
2. The orchestrator extracts URLs via regex and generates Playwright tests
3. **Smart Skip**: Compares file timestamps — if the `.py` test is newer than the `.txt` requirement, it asks: _"(1) Run existing / (2) Regenerate"_
4. Each test generates:
   - `generated_tests/test_[name].py` — executable Playwright test
   - `generated_tests/test_[name].md` — Markdown summary with status, model, errors, and self-healing details
   - `reports/report_[timestamp].html` — professional HTML report

---

## 📊 Provider Benchmarks

| Provider                        | Status    | Highlighted Capability                                                             |
| ------------------------------- | --------- | ---------------------------------------------------------------------------------- |
| **OpenAI (GPT-4o-mini)**        | ✅ Passed | **High-Speed Precision:** Optimal for complex logic generation with lowest latency |
| **Google (Gemini 3 Flash)**     | ✅ Passed | **Fault Tolerance:** Demonstrated auto-recovery during API 503 unavailability      |
| **OpenRouter (DeepSeek V4) ⭐** | ✅ Passed | **Recommended Cloud:** Best price/performance ratio for batch generation           |
| **Local (Qwen 2.5:3b)**         | ✅ Passed | **Zero-Cost Privacy:** 100% offline execution optimized for Apple Silicon (M2)     |

---

## 🖼️ Visual Overview

### 1. Main Menu & Multi-LLM Provider Selection

![Main Menu](assets/main_menu.png)

> The structured CLI interface (English-only) presents two distinct selection blocks — **Mode** (Interactive vs. Batch) and **AI Provider** (Local Ollama, OpenAI GPT-4o-mini, Google Gemini 3 Flash, or OpenRouter DeepSeek V4). In this example, **DeepSeek V4** is selected, followed by a successful `login_test` execution demonstrating seamless batch processing.

### 2. AI Self-Healing & Smart Error Classification

![AI Self-Healing Process](assets/self_healing.png)

> When a test fails, the orchestrator automatically classifies the error type (Selector vs. Assertion), analyzes the DOM state, and applies an autonomous fix. The terminal output shows the full healing cycle: error detection → `🔍 Error type: selector` → `🧠 Diagnosis` (identifying that `#palyanytsya` is missing and the correct selector is `#username`) → `✨ AI FIX APPLIED` → test retry → `✅ TEST PASSED SUCCESSFULLY`. This eliminates flaky tests and reduces maintenance overhead by approximately 80%.

### 3. Professional HTML Report & Markdown Summary

![HTML Report Preview](assets/report_preview.png)

> A high-fidelity Bootstrap-based report featuring a red **FAILED** badge, a full Python traceback of a `TimeoutError`, and a **Failure Screenshot** section capturing the actual web page at the moment of failure. Each test execution generates this stakeholder-ready HTML artifact along with a Markdown summary (`test_[name].md`) providing test status, AI model used, error details, and self-healing history — enabling rapid audit and traceability for QA leadership.

---

## 🛠 Tech Stack

- **Core**: Python 3.9+, AsyncIO
- **Browser Automation**: Playwright (Async API)
- **DOM Processing**: Custom BeautifulSoup4 Sanitizer (optimizes LLM token consumption)
- **Intelligence**: Google GenAI SDK, OpenAI API, OpenRouter API, Ollama (Local Models)
- **Optimization**: Apple Silicon (M2) native support for local LLM inference

---

## 🚀 Quick Start

### Prerequisites

```bash
pip install -r requirements.txt
playwright install
```

### Environment Setup

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key
OPENROUTER_API_KEY=your_openrouter_key
```

### Local LLM (Optional)

```bash
ollama pull qwen2.5:3b
```

### Run the Orchestrator

```bash
python3 main.py
```

You will be prompted to select:

1. **Mode**: Interactive (manual) or Batch (automatic from `requirements/`)
2. **Provider**: Local (Qwen), OpenAI, Google Gemini, or OpenRouter (DeepSeek V4)

---

## 🧠 Core Architecture

### CortexScraper

Cleans raw HTML, stripping scripts and CSS to provide LLMs with a structured, token-efficient DOM tree. Optimized to reduce token consumption by ~60% compared to raw HTML.

### CortexBridge

The intelligence layer that translates natural-language intent into executable Playwright Python code. Supports four providers with automatic failover and retry logic.

### CortexReporter

Aggregates test metadata (URL, task, status, error, screenshot) and constructs professional Bootstrap-based HTML artifacts for stakeholder visibility.

---

## 🧩 Repository Structure

```
Cortex-SDET/
├── main.py              # Orchestrator: CLI, Batch Mode, Smart Skip, Self-Healing
├── bridge.py            # AI Bridge: Multi-LLM support (OpenAI, Gemini, DeepSeek, Ollama)
├── reporter.py          # HTML report generator
├── scraper.py           # DOM sanitizer and HTML cleaner
├── requirements/        # Input: .txt files with test descriptions
├── generated_tests/     # Output: generated .py tests + .md summaries
├── reports/             # Output: professional HTML reports
├── assets/              # Screenshots for documentation
├── README.md
└── requirements.txt
```

---

_Designed and engineered by Oleksandr Dermanskij — AQA Engineer & AI Automation Specialist_
