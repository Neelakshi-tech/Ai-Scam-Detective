"""Data models for AI Scam Detective.

All models are pure data containers using Python dataclasses.
No business logic lives here.
"""

from dataclasses import dataclass, field


@dataclass
class Tactic:
    """A single scam tactic detected in a message."""

    tactic_id: str
    """Identifier from the approved taxonomy, e.g. 'URGENCY'."""

    tactic_name: str
    """Human-readable name, e.g. 'Urgency / Time Pressure'."""

    explanation: str
    """Plain-English explanation of why this is a warning sign."""

    evidence_quotes: list[str] = field(default_factory=list)
    """Exact phrases from the original message that triggered this tactic."""


@dataclass
class AnalysisResult:
    """The complete result of analyzing a suspicious message."""

    risk_level: str
    """Overall risk level: 'Low', 'Medium', 'High', or 'Unknown'."""

    risk_summary: str
    """One or two plain-English sentences summarising the risk."""

    tactics: list[Tactic] = field(default_factory=list)
    """List of detected scam tactics with evidence."""

    recommended_actions: list[str] = field(default_factory=list)
    """Safe steps the user should take."""

    learn_tactic_id: str = ""
    """ID of the primary tactic — used to look up the Learn card."""

    is_fallback: bool = False
    """True when AI analysis was unavailable and a fallback was used."""

    fallback_reason: str = ""
    """Short error category string when is_fallback=True (e.g. 'model_not_found').
    Safe to display; contains no secrets. Empty when analysis succeeded."""

    fallback_debug: str = ""
    """Sanitized exception message when is_fallback=True.
    Secrets are redacted. Shown only in the developer diagnostic expander."""


@dataclass
class DetectiveScenario:
    """A pre-written sample message used in Detective Mode."""

    scenario_id: str
    """Unique identifier for this scenario."""

    title: str
    """Short display title, e.g. 'Parcel Delivery Scam'."""

    message_text: str
    """The full sample message shown to the user."""

    phrases: list[str] = field(default_factory=list)
    """Selectable phrase options presented as checkboxes."""

    correct_phrase_indices: list[int] = field(default_factory=list)
    """Indices into `phrases` that are the correct suspicious clues."""

    explanation: str = ""
    """Feedback text explaining the correct answers after submission."""

    tactic_id: str = ""
    """Primary tactic ID for linking to the Learn section."""


@dataclass
class DetectiveResult:
    """The result of a user's Detective Mode attempt."""

    score: int
    """Score from 0 to 100."""

    correct_count: int
    """Number of correct phrases the user selected."""

    total_correct: int
    """Total number of correct phrases in the scenario."""

    missed_indices: list[int] = field(default_factory=list)
    """Indices of correct phrases the user did NOT select."""

    false_positive_indices: list[int] = field(default_factory=list)
    """Indices of phrases the user selected that were NOT correct."""

    feedback: str = ""
    """Plain-English feedback message."""
