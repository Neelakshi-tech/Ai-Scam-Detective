# AI Scam Detective — Implementation Plan

## Overview

Build a Streamlit web application that allows a user to paste a suspicious message
and receive a structured risk assessment, plain-language tactic explanations,
highlighted evidence, recommended safe actions, and a short educational takeaway.
The application also includes a Detective Mode where the user actively identifies
suspicious clues in a pre-written sample message, and a Learn page with static
educational content about common scam tactics.

Stack: Python 3.11+, Streamlit, Google Gemini API (google-genai SDK), pytest, python-dotenv.

Architecture: three layers — UI (Streamlit pages + shared components), Business
Logic (services), AI (prompt builder + API client + response parser). Data models
are Python dataclasses. Static content (scenarios, tactic library) lives in plain
Python dicts/lists — no database.

---

## Complexity Reductions Applied

| Original Requirement | Simplification Applied |
|---|---|
| Clickable phrase highlighting in Detective Mode | Checkbox list of numbered extracted phrases instead |
| Inline highlight of suspicious phrases in submitted text | st.markdown with mark tags via unsafe_allow_html |
| Full OOP everywhere | Dataclasses for data; service classes only where behavior belongs with state |
| Session score persistence | st.session_state only — no file or DB |
| Large Learn library | 6 static tactic cards in a Python dict |
| AI JSON reliability | Strict system prompt + parse fallback that extracts JSON from prose |
| Real URL checking | Regex pattern detection only — never resolve/fetch URLs |

---

## Final Feature List

### MVP (required for demo)
- Message paste + Analyze button with privacy disclaimer
- Risk level badge: Low / Medium / High with color and icon
- Risk summary sentence
- Tactic cards: name, explanation, quoted evidence from the message
- Highlighted message view with suspicious phrases marked
- Recommended safe actions list
- Educational takeaway card (one per analysis, based on primary tactic)
- Detective Mode: one scenario minimum, checkbox phrase selection, score + feedback
- Learn page: 6 static tactic info cards
- Graceful error handling for API failure or malformed response
- Session state tracking for Detective Mode score

### Optional (add if time allows)
- 2 additional Detective Mode scenarios
- Session score tracker shown in sidebar
- Share-friendly result layout (clean layout for screenshot)
- Additional tactic cards beyond 6

### Out of Scope
- User accounts, login, database
- Real-time URL resolution or visiting links
- Browser extension or mobile app
- Fine-tuned ML classifier
- Multi-language support

---

## User Flow

```
User opens app
    |
    +-- Analyze tab
    |     Paste message --> Analyze --> Risk badge + tactic cards
    |                              --> Highlighted message
    |                              --> Recommended actions
    |                              --> Learn card
    |
    +-- Detective Mode tab
    |     View sample message --> Select suspicious phrases --> Submit
    |                        --> Score + correct answer feedback
    |
    +-- Learn tab
          Browse 6 tactic cards (no interaction required)
```

---

## Application Architecture

```
UI Layer (Streamlit)
    app.py                  Navigation, session_state init
    pages/analyze_page.py   DETECT + EXPLAIN
    pages/detective_page.py INVESTIGATE
    pages/learn_page.py     EDUCATE
    ui/components.py        Shared rendering functions

Business Logic Layer
    services/analysis_service.py    Orchestrates pipeline
    services/detective_service.py   Scoring and scenario logic
    services/risk_assessor.py       Rule-based risk mapping
    services/validator.py           Input sanitization and validation

AI Layer
    ai/ai_analyzer.py   AIAnalyzer class: prompt, API call, parse
    ai/prompts.py       System and user prompt string templates

Data Layer (static, no DB)
    data/models.py          Dataclasses
    data/scenarios.py       Detective Mode sample scenarios
    data/tactics_library.py Static tactic education cards
```

---

## Project Folder Structure

```
AI_SCAM_DETECTIVE/
├── app.py
├── pages/
│   ├── analyze_page.py
│   ├── detective_page.py
│   └── learn_page.py
├── services/
│   ├── analysis_service.py
│   ├── detective_service.py
│   ├── risk_assessor.py
│   └── validator.py
├── ai/
│   ├── ai_analyzer.py
│   └── prompts.py
├── data/
│   ├── models.py
│   ├── scenarios.py
│   └── tactics_library.py
├── ui/
│   └── components.py
├── tests/
│   ├── test_validator.py
│   ├── test_risk_assessor.py
│   ├── test_ai_analyzer.py
│   └── test_detective_service.py
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Data Models (data/models.py)

All models are Python dataclasses with type hints.

```
Tactic
    tactic_id: str              e.g. "URGENCY"
    tactic_name: str            e.g. "Urgency / Time Pressure"
    explanation: str            plain-English explanation
    evidence_quotes: list[str]  exact phrases copied from original message

AnalysisResult
    risk_level: str             "Low" | "Medium" | "High"
    risk_summary: str           1-2 sentence verdict in plain language
    tactics: list[Tactic]       detected tactics with evidence
    recommended_actions: list[str]
    learn_tactic_id: str        ID of primary tactic for the Learn card

DetectiveScenario
    scenario_id: str
    title: str
    message_text: str           full sample message text
    phrases: list[str]          selectable option phrases shown to user
    correct_phrase_indices: list[int]
    explanation: str            feedback text shown after submission

DetectiveResult
    score: int                  0 to 100
    correct_count: int
    total_correct: int
    feedback: str
```

---

## Module Responsibilities

### services/validator.py
Pure functions only. No class needed.

    sanitize_input(text: str) -> str
        Strip HTML tags with regex. Normalize whitespace. Return clean string.

    validate_length(text: str) -> tuple[bool, str]
        Return (True, "") if 10 <= len(text) <= 2000.
        Return (False, error_message) otherwise.

### services/risk_assessor.py
Pure functions only.

    HIGH_SEVERITY_TACTIC_IDS: list[str]
        ["CREDENTIAL_REQUEST", "MONEY_REQUEST", "FEAR", "SUSPICIOUS_LINK"]

    assess_risk(tactics: list[Tactic]) -> str
        Apply escalation rules:
            0 tactics -> "Low"
            Any high-severity tactic -> at least "Medium"
            2+ high-severity tactics -> "High"
            CREDENTIAL_REQUEST or MONEY_REQUEST alone -> "High"
            1-2 low-severity tactics -> "Low"
            3+ low-severity tactics -> "Medium"
        Return "Low" | "Medium" | "High"

### ai/prompts.py
String constants only.

    SYSTEM_PROMPT: str
        Instructs the AI to:
        - Act as a cybersecurity educator
        - Return ONLY valid JSON matching the output schema
        - Use risk-oriented language, never "this is definitely a scam"
        - Never request or repeat user credentials
        - Never invent evidence not present in the message
        - Identify only the tactic IDs from the approved taxonomy
        - Keep explanations in plain English, no jargon

    USER_PROMPT_TEMPLATE: str
        Template that inserts the sanitized message text.
        Includes the JSON schema the AI must follow.
        Lists all valid tactic IDs.

### ai/ai_analyzer.py — class AIAnalyzer
    __init__(self, api_client)
        Accept an injected API client (allows mocking in tests).

    analyze(self, message_text: str) -> AnalysisResult
        Calls _build_messages, _call_api, _parse_response.
        On any exception, returns _fallback_result().

    _build_messages(self, text: str) -> list[dict]
        Constructs the messages list: system prompt + user prompt with text.

    _call_api(self, messages: list[dict]) -> str
        Calls the AI API. Returns raw response content as string.

    _parse_response(self, raw: str) -> AnalysisResult
        1. Try to parse raw as JSON directly.
        2. If that fails, search for a JSON block in the string.
        3. Map parsed dict to AnalysisResult and Tactic dataclasses.
        4. Validate required fields are present.
        5. On failure, raise ValueError.

    _fallback_result(self) -> AnalysisResult
        Returns a safe generic AnalysisResult with:
        - risk_level = "Unknown"
        - risk_summary = friendly message explaining analysis was unavailable
        - tactics = []
        - recommended_actions = generic safe advice list
        - learn_tactic_id = ""

### services/analysis_service.py — class AnalysisService
    __init__(self, analyzer: AIAnalyzer)
        Accept injected AIAnalyzer.

    run(self, raw_text: str) -> tuple[AnalysisResult | None, str | None]
        1. validate_length(raw_text) -- return (None, error_msg) if invalid
        2. sanitize_input(raw_text) -> clean_text
        3. analyzer.analyze(clean_text) -> result
        4. assess_risk(result.tactics) -> rule_risk
        5. Override result.risk_level if rule_risk is higher severity.
        6. Return (result, None)

### services/detective_service.py — class DetectiveService
    get_scenario(self, scenario_id: str) -> DetectiveScenario
        Return scenario by ID from scenarios.py list.

    get_all_scenarios(self) -> list[DetectiveScenario]
        Return all available DetectiveScenario objects.

    score_attempt(self, scenario: DetectiveScenario,
                  selected_indices: list[int]) -> DetectiveResult
        Compare selected_indices against scenario.correct_phrase_indices.
        correct_count = len(intersection of selected and correct).
        false_positives = len(selected) - correct_count.
        score = max(0, round((correct_count / len(correct)) * 100
                             - false_positives * 10))
        Build feedback string.
        Return DetectiveResult.

### ui/components.py
Pure Streamlit rendering functions. No business logic.

    render_disclaimer() -> None
        Renders a yellow st.warning banner with privacy and safety notice.

    render_risk_badge(risk_level: str) -> None
        Maps risk_level to color emoji and label.
        Renders via st.markdown with inline HTML span for color.

    render_highlighted_message(text: str, quotes: list[str]) -> None
        For each quote, wraps it in an HTML mark tag in the text string.
        Renders via st.markdown(unsafe_allow_html=True).

    render_tactic_cards(tactics: list[Tactic]) -> None
        For each tactic, renders an st.expander.
        Inside: tactic name, explanation, evidence quotes as blockquotes.

    render_actions(actions: list[str]) -> None
        Renders each action as a bullet with a checkmark emoji.

    render_learn_card(tactic_id: str) -> None
        Looks up tactic_id in tactics_library.
        Renders title, description, example, and tip in an st.info block.

---

## AI Prompt Design

### System Prompt Intent
The system prompt in prompts.py must establish:
1. Role: "You are a cybersecurity educator who helps people understand suspicious messages."
2. Task: "Analyze the message and return ONLY valid JSON. Do not write any prose."
3. Taxonomy: List of valid tactic IDs the AI may use.
4. Language rules: Use "High Risk signals detected", never "this is a scam".
5. Evidence rule: Only quote text that is literally present in the message.
6. Credential rule: If the message contains passwords or OTPs, do NOT include them in your response.
7. Schema: Provide the exact JSON structure the AI must return.

### User Prompt Template Intent
The user prompt inserts the sanitized message and reminds the AI of the JSON schema.
It also passes the list of valid tactic IDs as a reference.

### AI Output JSON Schema

```json
{
  "risk_level": "Low | Medium | High",
  "risk_summary": "string (1-2 sentences, plain English)",
  "tactics": [
    {
      "tactic_id": "string (from approved taxonomy)",
      "tactic_name": "string",
      "explanation": "string (plain English)",
      "evidence_quotes": ["string", "..."]
    }
  ],
  "recommended_actions": ["string", "..."],
  "learn_tactic_id": "string (primary tactic ID)"
}
```

### Valid Tactic ID Taxonomy

| ID | Name |
|---|---|
| URGENCY | Urgency / Time Pressure |
| FEAR | Fear or Threat |
| AUTHORITY | Fake Authority |
| MONEY_REQUEST | Request for Money / Payment |
| CREDENTIAL_REQUEST | Request for Password / OTP / Credentials |
| SUSPICIOUS_LINK | Suspicious Link or Domain |
| REWARD | Unrealistic Reward or Offer |
| JOB_SCAM | Fake Job or Investment Opportunity |
| IMPERSONATION | Impersonation of Known Brand or Person |
| INFO_HARVEST | Personal Information Harvesting |

---

## Risk Assessment Rules (risk_assessor.py)

Two-layer approach:
- Layer 1: AI returns a suggested risk_level in its JSON.
- Layer 2: risk_assessor.assess_risk() applies rule-based override.

If the rule-based result is HIGHER severity than the AI result, override it.
Never downgrade the AI result with the rule-based check.

Severity ladder (ascending): Low -> Medium -> High

Override rules applied in order:
1. CREDENTIAL_REQUEST or MONEY_REQUEST present -> High (regardless of count)
2. 2+ high-severity tactics present -> High
3. Any single high-severity tactic present -> at least Medium
4. 3+ low-severity tactics -> Medium
5. Default -> Low

---

## Input / Output Schema

### Input to analysis_service.run()
    raw_text: str   (user-provided, unvalidated)

### Output of analysis_service.run()
    (AnalysisResult, None)   on success
    (None, str)              on validation error; str is user-facing message

### Input to AIAnalyzer.analyze()
    message_text: str   (already sanitized by this point)

### Output of AIAnalyzer.analyze()
    AnalysisResult dataclass (never raises; returns fallback on failure)

---

## Validation and Privacy Safeguards

### Input validation
- Minimum 10 characters; maximum 2000 characters.
- HTML tags stripped before any further processing.
- Whitespace normalized.
- Validation error shown inline, not as an exception.

### Privacy safeguards
- No message text written to disk, database, or log files.
- API key stored in .env, never in source code, never sent to frontend.
- System prompt instructs AI to ignore/omit credential-like strings in the message.
- UI disclaimer shown above input: "Do not paste real passwords, OTPs,
  banking details, or card numbers. This tool is for educational awareness only."
- Session state (score) cleared when browser tab closes.

### Security safeguards
- URLs in messages are never fetched or resolved.
- No subprocess or eval calls anywhere in the codebase.
- AI response JSON is parsed with json.loads, not eval.
- All user-facing strings are rendered via Streamlit components (XSS safe
  except for the controlled unsafe_allow_html used only in components.py
  with sanitized input).

---

## Error and Fallback Strategy

| Scenario | Handling |
|---|---|
| Input too short | Inline st.warning: "Please paste the full message for a better analysis." |
| Input too long | Inline st.warning: "Message too long. Please paste the key section only." |
| API timeout or network error | Return _fallback_result(); show st.error with generic advice |
| API returns malformed JSON | Attempt JSON extraction from prose; if still failed, return fallback |
| AI returns unknown tactic ID | Ignore the tactic; do not crash |
| AI returns no tactics | Return Low risk with "No obvious warning signs detected — but stay cautious." |
| AI returns missing required field | Return fallback result |
| Detective scenario ID not found | Return first available scenario |

---

## Unit Test Plan

### tests/test_validator.py
- sanitize_input removes HTML tags
- sanitize_input normalizes multiple spaces
- validate_length: 9 chars -> invalid
- validate_length: 10 chars -> valid
- validate_length: 2000 chars -> valid
- validate_length: 2001 chars -> invalid
- validate_length: empty string -> invalid

### tests/test_risk_assessor.py
- Empty tactic list -> Low
- Single URGENCY tactic -> Low
- Two URGENCY tactics -> Low (both low-severity)
- Three low-severity tactics -> Medium
- Single FEAR tactic -> Medium
- Single CREDENTIAL_REQUEST tactic -> High
- Single MONEY_REQUEST tactic -> High
- URGENCY + SUSPICIOUS_LINK -> High (two high-severity)
- Mixed: REWARD + URGENCY + INFO_HARVEST -> Medium

### tests/test_ai_analyzer.py (all using mock API client)
- Valid JSON response -> correct AnalysisResult returned
- JSON embedded in prose -> extracted and parsed correctly
- Missing risk_level field -> fallback result returned
- Unknown tactic_id in response -> tactic skipped, no crash
- API raises exception -> fallback result returned
- Empty tactics list -> AnalysisResult with empty tactics returned

### tests/test_detective_service.py
- All correct selections -> score 100
- All wrong selections -> score 0
- Partial correct, no false positives -> proportional score
- Partial correct + false positives -> penalty applied
- score never goes below 0
- score_attempt returns DetectiveResult dataclass

---

## Manual UI Testing Plan

### Analyze page
- Paste a blank message -> validation warning shown, no API call made
- Paste 9-character message -> validation warning shown
- Paste a clean benign message -> Low risk result displayed correctly
- Paste the parcel delivery demo message -> High risk, 3+ tactic cards shown
- Paste the job offer demo message -> High risk, JOB_SCAM tactic shown
- Verify highlighted message marks at least one phrase
- Verify recommended actions list renders
- Verify learn card renders for primary tactic
- Verify disclaimer appears above input

### Detective Mode page
- Page loads with sample scenario message visible
- Phrases shown as checkboxes
- Submit with no selection -> prompt to select at least one
- Submit with all correct answers -> 100 score shown
- Submit with wrong answers -> score below 100, correct answers revealed
- Feedback text shown after submission

### Learn page
- All 6 tactic cards visible
- Each card shows name, description, example, and tip

### Error states
- Simulate API failure (set invalid API key) -> graceful error message shown
- Verify no stack trace shown to user

---

## Demo Messages (Safe, Pre-Written)

### Demo 1 — Parcel Delivery Scam (High Risk)
```
Your parcel could not be delivered today. A redelivery fee of £2.99 is required
within 24 hours or your parcel will be returned to sender. Please pay immediately
at: royalm4il-delivery-fees.com. Failure to pay will result in a £15 storage fee.
```
Expected: High risk. Tactics: URGENCY, MONEY_REQUEST, SUSPICIOUS_LINK, FEAR.

### Demo 2 — Fake Job Offer (High Risk)
```
Hi! We found your CV online and would love to offer you a work-from-home position
earning up to £800 per day. No experience needed. To secure your spot, please
send a registration fee of £49 and provide your bank account details for payroll
setup. Offer expires tonight!
```
Expected: High risk. Tactics: JOB_SCAM, MONEY_REQUEST, URGENCY, INFO_HARVEST.

### Demo 3 — Bank Impersonation (High Risk)
```
URGENT: Unusual activity detected on your Barclays account. Your account has been
temporarily suspended. Verify your identity immediately by entering your full card
number, PIN and one-time passcode at: barclays-secure-verify.net
```
Expected: High risk. Tactics: FEAR, AUTHORITY, IMPERSONATION, CREDENTIAL_REQUEST, SUSPICIOUS_LINK.

### Demo 4 — Prize Winner Scam (Medium Risk)
```
Congratulations! You have been selected as our lucky winner this month.
To claim your £500 Amazon gift card, simply reply with your full name,
home address and date of birth. This offer is valid for 48 hours only.
```
Expected: Medium-High risk. Tactics: REWARD, INFO_HARVEST, URGENCY.

### Demo 5 — Clean / Benign Message (Low Risk)
```
Hi, just a reminder that your dentist appointment is tomorrow at 10am.
Please call us on 01234 567890 if you need to reschedule. See you then!
```
Expected: Low risk. No significant tactics detected.

---

## Hackathon Demonstration Sequence

Step 1 (0:00)
    Open app. Show clean, professional home page with disclaimer.

Step 2 (0:30)
    Paste Demo 1 (parcel delivery). Click Analyze.

Step 3 (1:00)
    Result appears: HIGH RISK badge in red.
    Walk through the risk summary sentence.

Step 4 (1:30)
    Walk through tactic cards:
    - "Urgency: 'within 24 hours'"
    - "Money Request: 'redelivery fee of £2.99'"
    - "Suspicious Link: 'royalm4il-delivery-fees.com'"

Step 5 (2:00)
    Show highlighted message view — suspicious phrases marked in the original text.

Step 6 (2:20)
    Show Recommended Actions checklist.

Step 7 (2:40)
    Show Learn card for SUSPICIOUS_LINK.

Step 8 (3:00)
    Switch to Detective Mode tab.
    Load the pre-written scenario.

Step 9 (3:20)
    Check a couple of correct phrase checkboxes. Submit.
    Score appears. Correct answers highlighted with feedback.

Step 10 (3:50)
    Quick tour of Learn tab — show 2 tactic cards.

Step 11 (4:20)
    Paste Demo 5 (benign dentist reminder).
    Result: LOW RISK in green. "No obvious warning signs detected."

Step 12 (4:40)
    Closing statement:
    "It turns a scary moment of uncertainty into a learning experience —
    explaining not just the risk but the manipulation tactic behind it."

---

## Implementation Order

Each step below is a self-contained subtask intended to be built and tested
before moving to the next. Dependencies are noted.

---

### Subtask 1 — Project scaffolding
Status: [ ] pending

Intent:
    Set up the project skeleton, dependency management, and configuration.
    This must be done first — everything else depends on it.

Expected Outcomes:
    - requirements.txt exists with all dependencies pinned
    - .gitignore excludes .env, __pycache__, .pytest_cache
    - .env.example documents the required API key variable
    - All package directories (pages/, services/, ai/, data/, ui/, tests/) exist
      with empty __init__.py files
    - README.md updated with setup and run instructions
    - streamlit run app.py starts without errors (empty shell app)

Todo:
    1. Create requirements.txt (streamlit, google-genai, python-dotenv, pytest)
    2. Create .gitignore
    3. Create .env.example with GEMINI_API_KEY=your_key_here placeholder
    4. Create all package directories with __init__.py files
    5. Create empty app.py that renders "AI Scam Detective" as a title
    6. Update README.md with setup instructions

---

### Subtask 2 — Data models
Status: [ ] pending
Depends on: Subtask 1

Intent:
    Define all dataclasses used throughout the application.
    These are pure data containers — no logic, no imports from other app modules.

Expected Outcomes:
    - data/models.py contains Tactic, AnalysisResult, DetectiveScenario,
      DetectiveResult dataclasses
    - All fields have type hints
    - All dataclasses have a docstring

Todo:
    1. Create data/models.py with the four dataclasses as defined in this plan

---

### Subtask 3 — Static data content
Status: [ ] pending
Depends on: Subtask 2

Intent:
    Write the static content that powers the Learn page and Detective Mode.
    This is pure Python data — no business logic.

Expected Outcomes:
    - data/tactics_library.py contains a dict TACTICS_LIBRARY mapping
      tactic ID string to dict with keys: name, description, example, tip
    - 10 tactic entries present (one per tactic in the taxonomy)
    - data/scenarios.py contains a list SCENARIOS of at least 1 DetectiveScenario
    - Each scenario has a meaningful message_text, 6-8 phrase options,
      2-3 correct answers, and a clear explanation

Todo:
    1. Create data/tactics_library.py with 10 tactic entries
    2. Create data/scenarios.py with 1 DetectiveScenario (the parcel scam)
    3. Write phrases list for the scenario (mix of correct and distractor phrases)

---

### Subtask 4 — Validator and risk assessor
Status: [ ] pending
Depends on: Subtask 2

Intent:
    Implement pure business logic functions for input validation and risk
    level calculation. These have no external dependencies and can be fully
    unit tested.

Expected Outcomes:
    - services/validator.py implements sanitize_input and validate_length
    - services/risk_assessor.py implements assess_risk and HIGH_SEVERITY_TACTIC_IDS
    - All unit tests in test_validator.py and test_risk_assessor.py pass

Todo:
    1. Create services/validator.py
    2. Create services/risk_assessor.py
    3. Create tests/test_validator.py with all test cases from unit test plan
    4. Create tests/test_risk_assessor.py with all test cases from unit test plan
    5. Run pytest and confirm all pass

---

### Subtask 5 — AI analyzer
Status: [ ] pending
Depends on: Subtask 2, 4

Intent:
    Implement the AI prompt builder, API client wrapper, and response parser.
    This is the highest-risk module — mock tests must cover failure paths.

Expected Outcomes:
    - ai/prompts.py contains SYSTEM_PROMPT and USER_PROMPT_TEMPLATE
    - ai/ai_analyzer.py implements AIAnalyzer class with all methods
    - _parse_response correctly maps AI JSON to AnalysisResult
    - _fallback_result returns a valid safe AnalysisResult
    - All unit tests in test_ai_analyzer.py pass using mock API client
    - Real API call tested manually with at least one demo message

Todo:
    1. Create ai/prompts.py with system prompt and user prompt template
    2. Create ai/ai_analyzer.py with AIAnalyzer class
    3. Create tests/test_ai_analyzer.py with mock-based tests
    4. Run pytest and confirm all pass
    5. Test manually with a real API key and Demo 1 message

---

### Subtask 6 — Analysis service
Status: [ ] pending
Depends on: Subtask 4, 5

Intent:
    Implement the orchestration layer that connects validation, AI analysis,
    and risk override into a single run() call for the UI layer to use.

Expected Outcomes:
    - services/analysis_service.py implements AnalysisService.run()
    - run() returns (AnalysisResult, None) on success
    - run() returns (None, error_str) on validation failure
    - Risk level is overridden correctly when rule-based level is higher
    - Can be exercised manually end-to-end via a simple script

Todo:
    1. Create services/analysis_service.py
    2. Write a quick manual smoke test script (not committed) to call run()
       with Demo 1 and print the result

---

### Subtask 7 — Detective service
Status: [ ] pending
Depends on: Subtask 2, 3

Intent:
    Implement the scoring logic for Detective Mode.

Expected Outcomes:
    - services/detective_service.py implements DetectiveService
    - get_scenario, get_all_scenarios, score_attempt all work correctly
    - All unit tests in test_detective_service.py pass

Todo:
    1. Create services/detective_service.py
    2. Create tests/test_detective_service.py with all test cases from unit test plan
    3. Run pytest and confirm all pass

---

### Subtask 8 — Shared UI components
Status: [ ] pending
Depends on: Subtask 2, 3

Intent:
    Implement all reusable Streamlit rendering functions. These have no business
    logic — they only take data and render it.

Expected Outcomes:
    - ui/components.py implements all six render functions
    - Each function is independently callable and renders without errors
    - render_highlighted_message correctly wraps quotes in mark tags
    - render_risk_badge shows correct color/icon for each level

Todo:
    1. Create ui/components.py with all render functions
    2. Add a simple __main__ block or manual smoke check for each function

---

### Subtask 9 — Analyze page
Status: [ ] pending
Depends on: Subtask 6, 8

Intent:
    Build the main DETECT + EXPLAIN user experience. This is the core page
    and must be polished for the demo.

Expected Outcomes:
    - pages/analyze_page.py renders correctly
    - Disclaimer shown above textarea
    - Analyze button calls AnalysisService.run()
    - On success: risk badge, highlighted message, tactic cards, actions,
      learn card all render correctly
    - On validation error: inline warning shown
    - On API error: st.error with fallback advice shown
    - Manual UI test checklist for this page passes

Todo:
    1. Create pages/analyze_page.py
    2. Integrate AnalysisService with injected AIAnalyzer
    3. Use st.session_state to hold last result (avoids re-running on widget interaction)
    4. Apply the manual UI test checklist from this plan

---

### Subtask 10 — Detective Mode page
Status: [ ] pending
Depends on: Subtask 7, 8

Intent:
    Build the INVESTIGATE experience. Must be interactive and educational.

Expected Outcomes:
    - pages/detective_page.py renders a scenario with message text visible
    - Phrases shown as st.checkbox items
    - Submit button calls DetectiveService.score_attempt()
    - Score and feedback rendered after submission
    - At least one correct answer selection path tested manually

Todo:
    1. Create pages/detective_page.py
    2. Integrate DetectiveService
    3. Store selected_indices in st.session_state
    4. Apply the manual UI test checklist from this plan

---

### Subtask 11 — Learn page
Status: [ ] pending
Depends on: Subtask 3, 8

Intent:
    Build the EDUCATE experience. This is a static browse page — no logic needed.

Expected Outcomes:
    - pages/learn_page.py renders all tactic cards from tactics_library
    - Each card shows name, description, example, and tip
    - Page is visually clean and readable

Todo:
    1. Create pages/learn_page.py
    2. Loop over TACTICS_LIBRARY and call render_learn_card for each entry

---

### Subtask 12 — App shell and navigation
Status: [ ] pending
Depends on: Subtask 9, 10, 11

Intent:
    Wire all pages together in app.py with sidebar navigation.
    Initialize session state. Apply consistent page config.

Expected Outcomes:
    - streamlit run app.py loads correctly
    - Sidebar has links/tabs to Analyze, Detective Mode, Learn
    - st.session_state initialized for score and last result
    - Page title and icon set correctly
    - App looks polished and consistent across all three pages

Todo:
    1. Update app.py with st.set_page_config (title, icon)
    2. Add sidebar navigation using st.sidebar.radio or st.tabs
    3. Initialize st.session_state keys at startup
    4. Route to correct page based on navigation selection

---

### Subtask 13 — Final polish and demo preparation
Status: [ ] pending
Depends on: Subtask 12

Intent:
    Final UI polish, demo message preparation, and end-to-end testing.
    Ensure the hackathon demo flow runs without issues.

Expected Outcomes:
    - All 5 demo messages tested end-to-end and produce expected results
    - Full manual UI test checklist passes
    - No unhandled exceptions on any page
    - README.md has clear setup and run instructions
    - .env.example is accurate
    - Demonstration sequence from this plan can be executed in under 5 minutes

Todo:
    1. Run all 5 demo messages through the analyzer and verify outputs
    2. Run full manual UI test checklist
    3. Run pytest — all tests pass
    4. Update README.md with final instructions
    5. Do a full end-to-end walkthrough of the demo sequence
    6. Optional: add session score display in sidebar if time allows
