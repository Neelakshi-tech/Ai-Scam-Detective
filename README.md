# AI Scam Detective

An AI-powered cybersecurity awareness assistant that helps users detect suspicious messages,
understand scam tactics, and learn how to stay safer online.

Designed with a focus on **India-relevant scam patterns** — including UPI fraud, KYC scams,
fake government notices, and work-from-home job scams.

---

## Presentation

📊 [View Project Presentation (Google Slides)](https://docs.google.com/presentation/d/1HPo00dNnm7IppKXgLOZsoauyaaMxNSF3/edit?usp=sharing&ouid=105503233833147575287&rtpof=true&sd=true)

---

## Team

**Team name:** DuoByte

**Members:** Neelakshi · Nikita

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

# Optional: change the model (default is gemini-3.6-flash)
# GEMINI_MODEL=gemini-3.6-flash
```

Older values such as `gemini-2.5-flash` are upgraded automatically, including
values copied from Gemini error messages that start with `models/`. If you set
a custom model which has been retired, the app makes one safe retry with
`gemini-3.6-flash`.

Before starting the app after this update, refresh the Gemini SDK:

```bash
py -m pip install --upgrade -r requirements.txt
```

### What changed in this release

- Uses `gemini-3.6-flash` as the default Gemini model.
- Uses Gemini's Interactions API and an enforced JSON schema so analyses are
  returned as complete, displayable data rather than partial JSON.
- Repairs legacy model settings automatically, preventing the retired-model 404.
- Validates cleaned input, so pasted HTML cannot bypass the message-length check.
- Keeps the existing privacy-safe diagnostics: API keys are never displayed.

> **No API key?** The app runs in **fallback mode** — all features work (Detective Mode,
> Learn page, input validation, risk rules) except AI-powered message analysis.
> A clearly labeled notice is shown when fallback mode is active.
> The sidebar shows a warning if no key is configured.

### 3. Run the application

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

> Open the application at the root URL (for example, `http://localhost:8501`).
> Use the navigation inside the app; it is the single supported menu.

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
├── views/
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

## Built with IBM Bob

IBM Bob was the primary AI development partner used throughout this project — from initial architecture through implementation, debugging, and iterative refinement. All three of Bob's built-in modes were used in the way each is designed to be used.

### Plan mode — architecture and technical specification

The project started in **Plan mode**, Bob's read-only planning mode for designing architecture before writing any code. A natural-language brief describing the goal was submitted to Bob. Bob read the brief, asked clarifying questions about scope and complexity trade-offs, and produced [`scam-detective-plan.md`](scam-detective-plan.md): a structured implementation plan covering the full three-tier architecture, all data models, module responsibilities, AI prompt design, risk assessment rules, a 13-subtask ordered implementation sequence, a unit test plan, and five pre-written India-context demo messages. This document became the persistent source of truth for every subsequent coding session.

### Agent mode — feature implementation and debugging

With the plan approved, each implementation subtask was executed in **Agent mode** — Bob's code-writing mode that reads, creates, and modifies files across the full codebase. Bob implemented every layer:

- **Data layer:** `data/models.py` (Python dataclasses), `data/scenarios.py` (India-context Detective Mode scenarios), `data/tactics_library.py` (six static tactic education cards).
- **Services layer:** `services/validator.py`, `services/risk_assessor.py`, `services/analysis_service.py`, `services/detective_service.py`.
- **AI layer:** `ai/prompts.py` with the structured Gemini system prompt and user prompt template, and `ai/ai_analyzer.py` with the full `AIAnalyzer` class including the Gemini API call, enforced JSON schema, and a JSON-from-prose fallback parser.
- **UI layer:** `ui/components.py` with all shared Streamlit rendering functions, and the three view modules in `views/`.
- **App shell:** `app.py` with page config, custom CSS theming, sidebar navigation, session state initialisation, and lazy-import page routing.

Agent mode was also used for every bug fix:

- **Retired Gemini model (404 error):** Bob identified the retired model name, updated the default to `gemini-3.6-flash`, and added an automatic model-repair path in `AIAnalyzer` that detects legacy names and retries transparently.
- **HTML injection bypassing validation:** Bob found that pasting HTML-rich clipboard content allowed text that passed the character-count check but contained no meaningful content. A plain-text extraction step was added to the validator.
- **Gemini partial-JSON responses:** Bob designed and implemented the JSON-from-prose fallback parser that uses regex extraction to salvage well-formed JSON embedded in a larger prose response.
- **Streamlit multi-page nav conflict:** Bob diagnosed the root cause (Streamlit's automatic `pages/` folder detection) and applied the minimal targeted fix — renaming the folder to `_pages_disabled/` — without touching any other file.

### Ask mode — codebase exploration

**Ask mode** — Bob's read-only explanation mode — was used throughout development to interrogate the codebase safely before making changes. This included tracing the Streamlit sidebar conflict, understanding session state flow across modules, and confirming the orchestration relationship between `AnalysisService`, `AIAnalyzer`, and `RiskAssessor` before the test suite was written.

### Test generation

Bob wrote the full pytest suite in Agent mode, covering 70+ unit tests across `tests/test_validator.py`, `tests/test_risk_assessor.py`, `tests/test_ai_analyzer.py`, and `tests/test_detective_service.py`. All AI analyzer tests use mock Gemini clients so the entire suite runs offline without a real API key.

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
