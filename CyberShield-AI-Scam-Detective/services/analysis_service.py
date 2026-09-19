"""Analysis service — orchestrates the DETECT → EXPLAIN pipeline.

AnalysisService is the single entry point for the UI layer.
It coordinates input validation, AI analysis, and risk-level override.
"""

from ai.ai_analyzer import AIAnalyzer
from data.models import AnalysisResult, Tactic
from services.risk_assessor import (
    HIGH_SEVERITY_TACTIC_IDS,
    assess_risk,
    escalate_risk,
)
from services.validator import sanitize_input, validate_length

# Tactic priority order used when deriving a fallback learn_tactic_id.
# Listed from most to least severe so the most educational tactic is shown.
_TACTIC_PRIORITY: list[str] = [
    "CREDENTIAL_REQUEST",
    "MONEY_REQUEST",
    "SUSPICIOUS_LINK",
    "FEAR",
    "AUTHORITY",
    "IMPERSONATION",
    "URGENCY",
    "JOB_SCAM",
    "REWARD",
    "INFO_HARVEST",
]


class AnalysisService:
    """Orchestrates the full message analysis pipeline.

    Usage:
        service = AnalysisService(AIAnalyzer())
        result, error = service.run(raw_text)
        if error:
            show_error(error)
        else:
            show_result(result)
    """

    def __init__(self, analyzer: AIAnalyzer) -> None:
        """Initialize with an AIAnalyzer instance.

        Args:
            analyzer: The AI analyzer to use for semantic analysis.
                      Can be a mock for testing.
        """
        self._analyzer = analyzer

    def run(self, raw_text: str) -> tuple[AnalysisResult | None, str | None]:
        """Run the full analysis pipeline on raw user input.

        Steps:
          1. Validate length of input.
          2. Sanitize (strip HTML, normalize whitespace).
          3. Run AI analysis.
          4. Filter out evidence quotes that do not literally appear in the
             sanitized message text (prevents hallucinated evidence).
          5. Apply rule-based risk override if the rules indicate higher risk.
          6. Derive learn_tactic_id if the AI left it empty.

        Args:
            raw_text: Unvalidated text pasted by the user.

        Returns:
            A tuple of (AnalysisResult, None) on success,
            or (None, error_message_string) on validation failure.
        """
        clean_text = sanitize_input(raw_text)
        is_valid, error_msg = validate_length(clean_text)
        if not is_valid:
            return None, error_msg

        result = self._analyzer.analyze(clean_text)

        if not result.is_fallback:
            # Remove evidence quotes that do not literally exist in the message.
            result.tactics = _filter_evidence_quotes(result.tactics, clean_text)

            # Apply rule-based safety net: never downgrade, only escalate.
            rule_risk = assess_risk(result.tactics)
            result.risk_level = escalate_risk(result.risk_level, rule_risk)

            # Derive a sensible learn_tactic_id when the AI left it blank.
            if not result.learn_tactic_id and result.tactics:
                result.learn_tactic_id = _derive_learn_tactic_id(result.tactics)

        return result, None


def _filter_evidence_quotes(tactics: list[Tactic], message_text: str) -> list[Tactic]:
    """Remove evidence quotes that are not literally present in the message.

    This prevents the AI from hallucinating evidence that does not exist in
    the original message, which would break the highlighted message view and
    mislead the user.

    Args:
        tactics:      List of Tactic objects from the AI response.
        message_text: The sanitized message text to check quotes against.

    Returns:
        The same list with invalid evidence_quotes entries removed.
        Tactics whose entire evidence_quotes list was invalid are kept —
        the tactic itself may still be valid even without a quote.
    """
    for tactic in tactics:
        tactic.evidence_quotes = [
            q for q in tactic.evidence_quotes if q and q in message_text
        ]
    return tactics


def _derive_learn_tactic_id(tactics: list[Tactic]) -> str:
    """Pick the most educational tactic ID from the detected tactics list.

    Uses a priority order from most to least severe so the user learns
    about the most dangerous tactic first.

    Args:
        tactics: Non-empty list of detected Tactic objects.

    Returns:
        The tactic_id of the highest-priority tactic, or the first
        tactic's ID if none match the priority list.
    """
    detected_ids = {t.tactic_id for t in tactics}
    for tactic_id in _TACTIC_PRIORITY:
        if tactic_id in detected_ids:
            return tactic_id
    return tactics[0].tactic_id
