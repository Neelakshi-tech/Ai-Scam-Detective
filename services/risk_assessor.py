"""Rule-based risk level assessment for AI Scam Detective.

This module provides a safety-net override on top of the AI's suggested
risk level. If the rule-based assessment is more severe than what the AI
returned, the rule-based result wins. The AI result is never downgraded.
"""

from data.models import Tactic

# Severity ladder used for comparison
_SEVERITY_ORDER = {"Low": 0, "Medium": 1, "High": 2, "Unknown": 1}

# Tactic IDs that are always treated as high-severity
HIGH_SEVERITY_TACTIC_IDS: list[str] = [
    "CREDENTIAL_REQUEST",
    "MONEY_REQUEST",
    "FEAR",
    "SUSPICIOUS_LINK",
]


def assess_risk(tactics: list[Tactic]) -> str:
    """Calculate a risk level from the list of detected tactics.

    Rules are applied in order of descending severity:
      1. CREDENTIAL_REQUEST or MONEY_REQUEST present alone -> High
      2. Two or more high-severity tactics -> High
      3. Any single high-severity tactic -> Medium (at least)
      4. Three or more low-severity tactics -> Medium
      5. Default -> Low

    Args:
        tactics: List of Tactic objects returned by the AI analyzer.

    Returns:
        'Low', 'Medium', or 'High'.
    """
    if not tactics:
        return "Low"

    tactic_ids = [t.tactic_id for t in tactics]

    # Rule 1: credential or money request alone -> High
    auto_high = {"CREDENTIAL_REQUEST", "MONEY_REQUEST"}
    if auto_high.intersection(tactic_ids):
        return "High"

    high_severity_present = [tid for tid in tactic_ids if tid in HIGH_SEVERITY_TACTIC_IDS]
    low_severity_present = [tid for tid in tactic_ids if tid not in HIGH_SEVERITY_TACTIC_IDS]

    # Rule 2: two or more high-severity tactics -> High
    if len(high_severity_present) >= 2:
        return "High"

    # Rule 3: any single high-severity tactic -> at least Medium
    if high_severity_present:
        return "Medium"

    # Rule 4: three or more low-severity tactics -> Medium
    if len(low_severity_present) >= 3:
        return "Medium"

    return "Low"


def escalate_risk(ai_risk: str, rule_risk: str) -> str:
    """Return the higher of the two risk levels.

    The AI result is never downgraded — only escalated if the rule-based
    assessment is more severe.

    Args:
        ai_risk:   Risk level suggested by the AI ('Low', 'Medium', 'High').
        rule_risk: Risk level determined by assess_risk().

    Returns:
        The higher of the two risk levels.
    """
    ai_severity = _SEVERITY_ORDER.get(ai_risk, 1)
    rule_severity = _SEVERITY_ORDER.get(rule_risk, 0)
    if rule_severity > ai_severity:
        return rule_risk
    return ai_risk
