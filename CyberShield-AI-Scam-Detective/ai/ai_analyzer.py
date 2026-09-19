"""AI analyzer for AI Scam Detective.

AIAnalyzer wraps the Google Gemini API call, constructs the prompt,
parses the structured JSON response, and returns an AnalysisResult.

Uses the official google-genai SDK (google.genai).

If the API is unavailable or returns unparseable output, a safe
fallback result is returned instead of raising an exception.
"""

import json
import logging
import os
import re
import time

from google import genai
from google.genai import errors as genai_errors

from ai.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, VALID_TACTIC_IDS
from data.models import AnalysisResult, Tactic

logger = logging.getLogger(__name__)

# Use a stable, broadly available text model by default.  A different model can
# still be selected explicitly with GEMINI_MODEL.
_DEFAULT_MODEL = "gemini-3.6-flash"
# Models retired by Gemini are mapped automatically.  This lets existing
# .env files keep working after an application upgrade.
_RETIRED_MODEL_ALIASES = {
    "gemini-2.5-flash": _DEFAULT_MODEL,
    "gemini-2.5-flash-lite": _DEFAULT_MODEL,
}

# HTTP status codes that indicate a transient server-side problem.
# Only these codes are retried; all other errors fail immediately.
_TRANSIENT_CODES = frozenset({500, 502, 503, 504})

_MAX_RETRIES = 2          # up to 2 additional attempts after the first failure
_RETRY_BASE_DELAY = 1.0   # seconds; doubled on each subsequent retry

_GENERIC_ACTIONS = [
    "Do not click any links in the message.",
    "Do not reply with personal information.",
    "Contact the organisation directly using a number from their official website.",
    "If in doubt, delete or ignore the message.",
    "Report suspicious messages to your national cyber-reporting service.",
]

# Gemini Interactions API structured-output schema.  Enforcing the schema at
# the API boundary prevents partial prose or markdown from reaching the JSON
# parser and gives the UI predictable fields to render.
_ANALYSIS_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["risk_level", "risk_summary", "tactics", "recommended_actions", "learn_tactic_id"],
    "properties": {
        "risk_level": {"type": "string", "enum": ["Low", "Medium", "High"]},
        "risk_summary": {"type": "string"},
        "tactics": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["tactic_id", "tactic_name", "explanation", "evidence_quotes"],
                "properties": {
                    "tactic_id": {"type": "string", "enum": VALID_TACTIC_IDS},
                    "tactic_name": {"type": "string"},
                    "explanation": {"type": "string"},
                    "evidence_quotes": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "recommended_actions": {"type": "array", "items": {"type": "string"}},
        "learn_tactic_id": {"type": "string"},
    },
}


class AIAnalyzer:
    """Analyzes suspicious messages using the Google Gemini API.

    Uses the google-genai SDK (google.genai).

    Usage:
        analyzer = AIAnalyzer()
        result = analyzer.analyze("Your parcel awaits…")
    """

    def __init__(self, client=None, model: str | None = None) -> None:
        """Initialize the analyzer with an optional injected client (for testing).

        Args:
            client: A pre-configured google.genai.Client instance. If None, the
                    client is created lazily on the first analyze() call, reading
                    GEMINI_API_KEY from the environment at that moment. This avoids
                    the @st.cache_resource issue where the instance is constructed
                    before load_dotenv() has run, freezing a None client forever.
            model:  Gemini model name. Defaults to the GEMINI_MODEL env var
                    or 'gemini-3.6-flash'.
        """
        self._model_name = self._normalise_model_name(
            model or os.getenv("GEMINI_MODEL", _DEFAULT_MODEL)
        )

        if client is not None:
            # Injected client (used in tests — any object with a models.generate_content method)
            self._client: object | None = client
            self._client_injected = True
        else:
            # Defer client creation to the first analyze() call so that the env
            # variable is read after load_dotenv() has run, even if this instance
            # was created and cached by @st.cache_resource before that point.
            self._client = None
            self._client_injected = False

    def _ensure_client(self) -> None:
        """Lazily initialise the Gemini client from the environment if not yet set.

        Only called from analyze(). Has no effect if a client was already injected
        (test scenario) or successfully created on a previous call.
        """
        if self._client is not None or self._client_injected:
            return
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key or api_key == "your_gemini_api_key_here":
            return  # leave _client as None — analyze() will return fallback
        try:
            self._client = genai.Client(api_key=api_key)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to initialise Gemini client: %s", exc)
            # _client stays None — analyze() will return fallback

    @staticmethod
    def _normalise_model_name(model_name: str) -> str:
        """Return a supported model name from a user-friendly configuration value.

        Gemini error messages sometimes show names prefixed with ``models/``;
        the SDK accepts the short name used in ``GEMINI_MODEL``.  Legacy 2.5
        names are upgraded so an old local .env does not cause a 404.
        """
        cleaned = model_name.strip().removeprefix("models/")
        migrated = _RETIRED_MODEL_ALIASES.get(cleaned, cleaned)
        if migrated != cleaned:
            logger.warning("GEMINI_MODEL=%s is retired; using %s.", cleaned, migrated)
        return migrated or _DEFAULT_MODEL

    @staticmethod
    def _classify_error(exc: Exception) -> str:
        """Return a short error-category string for the given exception.

        Used for developer diagnostics only — never shown to end users verbatim.
        The string is safe to surface in the UI because it contains no secrets.

        Categories:
            no_api_key        — key absent or placeholder
            transient         — 500/502/503/504 (retried; only raised after all retries fail)
            model_not_found   — 404 from Gemini API (wrong / deprecated model name)
            auth_error        — 401/403 (invalid key, wrong key type, no permission)
            quota_exceeded    — 429 rate-limit / quota exhausted
            api_error         — other HTTP error from Gemini API
            parse_fail        — response received but JSON could not be extracted
            network_error     — connection / DNS / timeout failure
            unexpected        — anything else
        """
        if isinstance(exc, genai_errors.APIError):
            code = getattr(exc, "code", 0) or 0
            status = str(getattr(exc, "status", "")).upper()
            if code in _TRANSIENT_CODES or "UNAVAILABLE" in status:
                return "transient"
            if code == 404 or "NOT_FOUND" in status:
                return "model_not_found"
            if code in (401, 403) or "UNAUTHENTICATED" in status or "PERMISSION_DENIED" in status:
                return "auth_error"
            if code == 429 or "RESOURCE_EXHAUSTED" in status:
                return "quota_exceeded"
            return "api_error"
        if isinstance(exc, ValueError):
            return "parse_fail"
        name = type(exc).__name__.lower()
        if any(k in name for k in ("connection", "timeout", "network", "socket", "ssl")):
            return "network_error"
        return "unexpected"

    @staticmethod
    def _sanitize_error_message(exc: Exception) -> str:
        """Return a sanitized, human-readable error message safe to display in the UI.

        Redacts any value that looks like an API key (long alphanumeric strings)
        to ensure no secrets appear in the developer diagnostic panel.
        """
        import re as _re
        msg = str(exc)
        # Redact anything that looks like an API key or bearer token
        msg = _re.sub(r"AIza[0-9A-Za-z_\-]{30,}", "<REDACTED_API_KEY>", msg)
        msg = _re.sub(r"AQ\.[0-9A-Za-z_\-]{20,}", "<REDACTED_TOKEN>", msg)
        msg = _re.sub(r"Bearer [0-9A-Za-z_\-\.]{20,}", "Bearer <REDACTED>", msg)
        # Truncate to a safe display length
        if len(msg) > 500:
            msg = msg[:500] + "…"
        return msg

    def analyze(self, message_text: str) -> AnalysisResult:
        """Analyze a sanitized message and return a structured AnalysisResult.

        Never raises. Returns a fallback result on any failure.

        Args:
            message_text: Sanitized message text (HTML stripped, length validated).

        Returns:
            AnalysisResult with risk level, tactics, actions, and learn content.
            On failure, is_fallback=True and debug_error is set with a sanitized
            error category and message for developer diagnostics.
        """
        self._ensure_client()
        if self._client is None:
            return self._fallback_result(reason="no_api_key")
        try:
            # A valid schema should make this loop unnecessary, but retry once
            # if a network intermediary or an incomplete generation still
            # returns malformed JSON instead of showing an unusable result.
            for parse_attempt in range(2):
                raw = self._call_api_with_retry(message_text)
                try:
                    return self._parse_response(raw)
                except ValueError:
                    if parse_attempt:
                        raise
                    logger.warning("Gemini returned incomplete JSON; requesting a fresh structured response.")
        except Exception as exc:  # noqa: BLE001
            category = self._classify_error(exc)
            safe_msg = self._sanitize_error_message(exc)
            logger.warning("Gemini analysis failed [%s]: %s", category, safe_msg)
            return self._fallback_result(reason=category, debug_message=safe_msg)

    # ------------------------------------------------------------------
    # Private methods
    # ------------------------------------------------------------------

    def _call_api_with_retry(self, text: str) -> str:
        """Call the Gemini API, retrying up to _MAX_RETRIES times on transient errors.

        Only 5xx-class transient errors (500, 502, 503, 504 / UNAVAILABLE) are
        retried. Permanent errors (auth, quota, model-not-found, parse) are raised
        immediately so the caller can classify and fall back without wasting time.

        Raises:
            Any exception from the final attempt, letting analyze() handle it.
        """
        # A custom model is honoured first.  If it returns 404, try the current
        # supported default once.  This makes stale environment settings
        # recover automatically without retrying a permanent failure.
        model_names = (self._model_name,)
        if self._model_name != _DEFAULT_MODEL:
            model_names += (_DEFAULT_MODEL,)
        last_exc: Exception | None = None

        for model_index, model_name in enumerate(model_names):
            delay = _RETRY_BASE_DELAY
            for attempt in range(1 + _MAX_RETRIES):
                try:
                    return self._call_api(text, model_name)
                except Exception as exc:  # noqa: BLE001
                    category = self._classify_error(exc)
                    if category == "model_not_found" and model_index < len(model_names) - 1:
                        logger.warning(
                            "Gemini model %s was not found; trying %s.",
                            model_name,
                            model_names[model_index + 1],
                        )
                        break
                    if category != "transient":
                        raise
                    last_exc = exc
                    if attempt < _MAX_RETRIES:
                        logger.warning(
                            "Gemini transient error on %s, attempt %d/%d; retrying in %.0fs: %s",
                            model_name,
                            attempt + 1,
                            1 + _MAX_RETRIES,
                            delay,
                            self._sanitize_error_message(exc),
                        )
                        time.sleep(delay)
                        delay *= 2

            if model_index < len(model_names) - 1 and last_exc is not None:
                logger.warning(
                    "Gemini model %s stayed unavailable; trying fallback model %s.",
                    model_name,
                    model_names[model_index + 1],
                )

        # Preserve the final API error so callers report this as a temporary
        # service issue instead of an unrelated "unexpected" error.
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("Gemini retry loop ended without an API attempt")  # pragma: no cover

    def _call_api(self, text: str, model_name: str) -> str:
        """Send a schema-constrained request through Gemini's Interactions API."""
        user_content = USER_PROMPT_TEMPLATE.format(message_text=text)
        interaction = self._client.interactions.create(
            model=model_name,
            input=f"{SYSTEM_PROMPT}\n\n{user_content}",
            response_format={
                "type": "text",
                "mime_type": "application/json",
                "schema": _ANALYSIS_RESPONSE_SCHEMA,
            },
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 2048,
            },
        )
        output_text = getattr(interaction, "output_text", "")
        if isinstance(output_text, str):
            return output_text

        # Earlier Interactions SDK previews exposed text through ``outputs``.
        # Keep this small compatibility path so the parser never receives a
        # MagicMock/object instead of actual model text during an SDK upgrade.
        outputs = getattr(interaction, "outputs", [])
        if isinstance(outputs, list) and outputs:
            fallback_text = getattr(outputs[-1], "text", "")
            if isinstance(fallback_text, str):
                return fallback_text
        return ""

    def _parse_response(self, raw: str) -> AnalysisResult:
        """Parse the raw Gemini response string into an AnalysisResult.

        Attempts direct JSON parse first, then searches for a JSON block
        embedded in prose. Raises ValueError if neither succeeds.

        Args:
            raw: Raw string content from the Gemini response.

        Returns:
            Parsed AnalysisResult.

        Raises:
            ValueError: If the response cannot be parsed into the expected schema.
        """
        data = self._extract_json(raw)

        risk_level = str(data.get("risk_level", "Unknown"))
        if risk_level not in ("Low", "Medium", "High"):
            risk_level = "Unknown"

        risk_summary = str(data.get("risk_summary", "Analysis complete."))
        learn_tactic_id = str(data.get("learn_tactic_id", ""))

        tactics: list[Tactic] = []
        for item in data.get("tactics", []):
            tactic_id = str(item.get("tactic_id", ""))
            if tactic_id not in VALID_TACTIC_IDS:
                # Skip unrecognised tactic IDs rather than crashing
                continue
            tactics.append(
                Tactic(
                    tactic_id=tactic_id,
                    tactic_name=str(item.get("tactic_name", tactic_id)),
                    explanation=str(item.get("explanation", "")),
                    evidence_quotes=[str(q) for q in item.get("evidence_quotes", [])],
                )
            )

        recommended_actions: list[str] = [
            str(a) for a in data.get("recommended_actions", [])
        ]
        if not recommended_actions:
            recommended_actions = _GENERIC_ACTIONS

        return AnalysisResult(
            risk_level=risk_level,
            risk_summary=risk_summary,
            tactics=tactics,
            recommended_actions=recommended_actions,
            learn_tactic_id=learn_tactic_id,
            is_fallback=False,
        )

    @staticmethod
    def _extract_json(raw: str) -> dict:
        """Try to extract a JSON dict from the raw response string.

        Strategy:
          1. Parse directly as JSON.
          2. Strip markdown code fences and retry.
          3. Find the first {...} block in the string and parse that.

        Raises:
            ValueError: If no valid JSON dict can be found.
        """
        raw = raw.strip()

        # Strip markdown code fences if Gemini wraps JSON in ```json ... ```
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            raw = raw.strip()

        try:
            result = json.loads(raw)
            if isinstance(result, dict):
                return result
        except json.JSONDecodeError:
            pass

        # Try to find a JSON block embedded in prose
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group())
                if isinstance(result, dict):
                    return result
            except json.JSONDecodeError:
                pass

        raise ValueError(f"Could not extract JSON from Gemini response: {raw[:200]!r}")

    @staticmethod
    def _fallback_result(reason: str = "unknown", debug_message: str = "") -> AnalysisResult:
        """Return a safe generic result when AI analysis is unavailable.

        Args:
            reason:        Short category string (not shown to users).
            debug_message: Sanitized exception message for developer diagnostics.
                           Never contains secrets. Safe to display in the UI.

        Returns:
            A clearly labeled fallback AnalysisResult with debug info attached.
        """
        logger.info("Returning fallback result (reason=%s)", reason)
        return AnalysisResult(
            risk_level="Unknown",
            risk_summary=(
                "AI analysis is currently unavailable. "
                "The safe actions below are general guidance you can always follow."
            ),
            tactics=[],
            recommended_actions=_GENERIC_ACTIONS,
            learn_tactic_id="",
            is_fallback=True,
            fallback_reason=reason,
            fallback_debug=debug_message,
        )
