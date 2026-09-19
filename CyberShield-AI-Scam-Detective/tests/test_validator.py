"""Unit tests for services/validator.py."""

import pytest
from services.validator import sanitize_input, validate_length, MIN_LENGTH, MAX_LENGTH


class TestSanitizeInput:
    def test_strips_html_tags(self):
        result = sanitize_input("<b>Hello</b> <script>alert(1)</script>world")
        assert "<b>" not in result
        assert "<script>" not in result
        assert "Hello" in result
        assert "world" in result

    def test_normalizes_multiple_spaces(self):
        result = sanitize_input("hello    world")
        assert result == "hello world"

    def test_normalizes_newlines(self):
        result = sanitize_input("line one\n\nline two")
        assert result == "line one line two"

    def test_strips_leading_trailing_whitespace(self):
        result = sanitize_input("  hello  ")
        assert result == "hello"

    def test_plain_text_unchanged_content(self):
        result = sanitize_input("This is a normal message.")
        assert result == "This is a normal message."


class TestValidateLength:
    def test_empty_string_is_invalid(self):
        valid, msg = validate_length("")
        assert valid is False
        assert msg != ""

    def test_whitespace_only_is_invalid(self):
        valid, msg = validate_length("   ")
        assert valid is False

    def test_nine_chars_is_invalid(self):
        valid, msg = validate_length("a" * 9)
        assert valid is False

    def test_ten_chars_is_valid(self):
        valid, msg = validate_length("a" * MIN_LENGTH)
        assert valid is True
        assert msg == ""

    def test_max_length_is_valid(self):
        valid, msg = validate_length("a" * MAX_LENGTH)
        assert valid is True
        assert msg == ""

    def test_over_max_length_is_invalid(self):
        valid, msg = validate_length("a" * (MAX_LENGTH + 1))
        assert valid is False
        assert msg != ""

    def test_typical_message_is_valid(self):
        text = "Your parcel could not be delivered. Pay £2.99 at fake-link.com"
        valid, msg = validate_length(text)
        assert valid is True
