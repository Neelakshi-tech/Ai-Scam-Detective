"""Input sanitization and validation for AI Scam Detective."""

import re

MIN_LENGTH = 10
MAX_LENGTH = 2000


def sanitize_input(text: str) -> str:
    """Strip HTML tags and normalize whitespace from user input.

    Args:
        text: Raw string from the user.

    Returns:
        Cleaned string with HTML removed and whitespace normalized.
    """
    # Remove HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", text)
    # Collapse multiple whitespace characters into a single space
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def validate_length(text: str) -> tuple[bool, str]:
    """Check that the input meets the minimum and maximum length requirements.

    Args:
        text: The (already sanitized) input string.

    Returns:
        A tuple of (is_valid, error_message).
        error_message is an empty string when is_valid is True.
    """
    length = len(text.strip())
    if length == 0:
        return False, "Please paste a message to analyze."
    if length < MIN_LENGTH:
        return False, "Please paste the full message — it's too short to analyze reliably."
    if length > MAX_LENGTH:
        return (
            False,
            f"Message is too long ({length} characters). "
            f"Please paste the key part of the message (maximum {MAX_LENGTH} characters).",
        )
    return True, ""
