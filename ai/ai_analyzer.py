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

from google import genai
from google.genai import errors as genai_errors

from ai.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE, VALID_TACTIC_IDS
from data.models import AnalysisResult, Tactic

logger = logging.getLogger(__name__)

_DEFAULT_MODEL = "gemini-2.0-flash"

_GENERIC_ACTIONS = [
    "Do not click any links in the message.",
    "Do not reply with personal information.",
    "Contact the organisation directly using a number from their official website.",
    "If in doubt, delete or ignore the message.",
    "Report suspicious messages to your national cyber-reporting service.",
]


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
            client: A pre-configured google.genai.Client instance. If None, one is
                    created automatically using the GEMINI_API_KEY environment variable.
                    Set to None internally if no key is configured — analyze() will
                    then return a safe fallback result.
            model:  Gemini model name. Defaults to the GEMINI_MODEL env var
                    or 'gemini-2.0-flash'.
        """
        self._model_name = model or os.getenv("GEMINI_MODEL", _DEFAULT_MODEL)

        if client is not None:
            # Injected client (used in tests — any object with a models.generate_content method)
            self._client = client
        else:
            api_key = os.getenv("GEMINI_API_KEY", "")
            if not api_key or api_key == "your_gemini_api_key_here":
                self._client = None
            else:
                try:
                    self._client = genai.Client(api_key=api_key)
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Failed to initialise Gemini client: %s", exc)
                    self._client = None

    def analyze(self, message_text: str) -> AnalysisResult:
        """Analyze a sanitized message and return a structured AnalysisResult.

        Never raises. Returns a fallback result on any failure.

        Args:
            message_text: Sanitized message text (HTML stripped, length validated).

        Returns:
            AnalysisResult with risk level, tactics, actions, and learn content.
        """
        if self._client is None:
            return self._fallback_result(reason="no_api_key")
        try:
            raw = self._call_api(message_text)
            return self._parse_response(raw)
        except genai_errors.APIError as exc:
            logger.warning("Gemini API error: %s", exc)
            return self._fallback_result(reason="api_error")
        except Exception as exc:  # noqa: BLE001
            logger.warning("Unexpected error during AI analysis: %s", exc)
            return self._fallback_result(reason="unexpected")

    # ------------------------------------------------------------------
    # Private methods
    # ------------------------------------------------------------------

    def _call_api(self, text: str) -> str:
        """Send the prompt to the Gemini API and return the raw response text."""
        user_content = USER_PROMPT_TEMPLATE.format(message_text=text)
        response = self._client.models.generate_content(
            model=self._model_name,
            contents=user_content,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.2,
                max_output_tokens=1200,
                response_mime_type="application/json",
            ),
        )
        return response.text or ""

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
    def _fallback_result(reason: str = "unknown") -> AnalysisResult:
        """Return a safe generic result when AI analysis is unavailable.

        Args:
            reason: Short string describing why the fallback was triggered
                    (used only for logging/debugging, not shown to users).

        Returns:
            A clearly labeled fallback AnalysisResult.
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
        )
