# AI Scam Detective

An AI-powered cybersecurity awareness assistant that helps users detect suspicious messages, understand scam tactics, and learn how to stay safer online.

## What it does

**AI Scam Detective** guides you through four stages:

- 🔍 **DETECT** — Paste a suspicious message and get an instant risk assessment
- 💡 **EXPLAIN** — Understand *why* something is suspicious, not just *that* it is
- 🕵️ **INVESTIGATE** — Detective Mode: identify clues in sample scam messages
- 📚 **EDUCATE** — Learn about common scam tactics and how to spot them

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure your AI API key

```bash
cp .env.example .env
```

Open `.env` and replace `your_openai_api_key_here` with your real [OpenAI API key](https://platform.openai.com/api-keys).

> **No API key?** The application will run in demo mode with rule-based analysis and clearly labeled fallback responses.

### 3. Run the application

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

## Run the tests

```bash
pytest tests/ -v
```

## Project structure

```
AI_SCAM_DETECTIVE/
├── app.py                    Streamlit entry point and navigation
├── pages/
│   ├── analyze_page.py       DETECT + EXPLAIN — paste and analyze a message
│   ├── detective_page.py     INVESTIGATE — interactive clue-finding challenge
│   └── learn_page.py         EDUCATE — browse scam tactic explanations
├── services/
│   ├── analysis_service.py   Orchestrates the analysis pipeline
│   ├── detective_service.py  Detective Mode scoring logic
│   ├── risk_assessor.py      Rule-based risk level calculation
│   └── validator.py          Input sanitization and length validation
├── ai/
│   ├── ai_analyzer.py        AI prompt builder, API client, response parser
│   └── prompts.py            System and user prompt templates
├── data/
│   ├── models.py             Dataclasses: Tactic, AnalysisResult, etc.
│   ├── scenarios.py          Detective Mode sample scenarios
│   └── tactics_library.py   Static Learn section tactic cards
├── ui/
│   └── components.py         Shared Streamlit rendering functions
└── tests/                    Unit tests (pytest)
```

## Technologies used

- **Python 3.11+**
- **Streamlit** — web UI framework
- **OpenAI API** — AI analysis (gpt-4o-mini by default)
- **python-dotenv** — API key management
- **pytest** — unit testing

## Important notes

- This tool is for **educational awareness only** and does not constitute legal or security advice.
- **Do not paste real passwords, OTPs, banking details, or card numbers** into this application.
- Risk assessments use risk-oriented language. The application never claims to definitively confirm fraud.
- No submitted message text is stored or logged.
