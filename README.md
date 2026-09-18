# AI Scam Detective

An AI-powered cybersecurity awareness assistant that helps users detect suspicious messages,
understand scam tactics, and learn how to stay safer online.

Designed with a focus on **India-relevant scam patterns** — including UPI fraud, KYC scams,
fake government notices, and work-from-home job scams.

---

## What it does

**AI Scam Detective** guides you through four stages:

- 🔍 **DETECT** — Paste a suspicious message and get an instant risk assessment
- 💡 **EXPLAIN** — Understand *why* something is suspicious, not just *that* it is
- 🕵️ **INVESTIGATE** — Detective Mode: identify clues in India-context sample scam messages
- 📚 **EDUCATE** — Learn about common scam tactics and how to spot them

The tool uses **risk-oriented language** — it never claims a message is "definitely a scam."
It explains which patterns were detected and lets you make an informed decision.

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure your Gemini API key

```bash
cp .env.example .env
```

Open `.env` and replace `your_gemini_api_key_here` with your real API key.

Get a free Gemini API key at **https://aistudio.google.com/app/apikey**

```env
GEMINI_API_KEY=AIza...your_real_key_here

# Optional: change the model (default is gemini-2.0-flash)
# GEMINI_MODEL=gemini-2.0-flash
```

> **No API key?** The app runs in **fallback mode** — all features work (Detective Mode,
> Learn page, input validation, risk rules) except AI-powered message analysis.
> A clearly labeled notice is shown when fallback mode is active.
> The sidebar shows a warning if no key is configured.

### 3. Run the application

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## Run the tests

```bash
pytest tests/ -v
```

All 70+ unit tests run without a real API key. The AI analyzer tests use mock clients.

---

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
│   ├── ai_analyzer.py        Gemini API client, prompt builder, response parser
│   └── prompts.py            System and user prompt templates
├── data/
│   ├── models.py             Dataclasses: Tactic, AnalysisResult, etc.
│   ├── scenarios.py          Detective Mode sample scenarios (India-context)
│   └── tactics_library.py   Static Learn section tactic cards
├── ui/
│   └── components.py         Shared Streamlit rendering functions
└── tests/                    Unit tests (pytest)
```

---

## Technologies used

| Library | Purpose |
|---|---|
| **Python 3.11+** | Language |
| **Streamlit** | Web UI framework |
| **google-genai** | Google Gemini API client (official SDK) |
| **python-dotenv** | `.env` file loading |
| **pytest** | Unit testing |

---

## Demo messages (India-context, fictional)

The Analyze page includes these pre-loaded demo messages:

| Demo | Expected Risk |
|---|---|
| 📦 Fake Delivery / Refund (UPI) | High — CREDENTIAL_REQUEST, URGENCY, SUSPICIOUS_LINK |
| 🏦 Fake KYC / Bank SMS | High — IMPERSONATION, CREDENTIAL_REQUEST, FEAR |
| 💼 Fake Work-from-Home Job | High — JOB_SCAM, MONEY_REQUEST, URGENCY |
| 🏛️ Fake Income Tax Refund | High — AUTHORITY, SUSPICIOUS_LINK, CREDENTIAL_REQUEST |
| 🎁 Fake Prize / Lucky Draw | High — REWARD, INFO_HARVEST, URGENCY |
| 📅 Normal Message (Low Risk) | Low — no significant warning signs |

---

## Important notes

- This tool is for **educational awareness only** and does not constitute legal or security advice.
- **Do not paste real passwords, OTPs, banking details, or card numbers** into this application.
- Risk assessments use risk-oriented language. The application never claims to definitively confirm fraud.
- No submitted message text is stored or logged.
- All demo messages use entirely **fictional** organisation names, URLs, amounts, and identifiers.
  No affiliation with or impersonation of real institutions is intended.
- Reporting links (cybercrime.gov.in, helpline 1930, TRAI 1909) are publicly available official
  resources. This tool is not affiliated with or endorsed by any government body.
