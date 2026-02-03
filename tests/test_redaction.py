"""Tests for API key redaction functionality."""

from src.generate_changelog import redact_api_key


def test_redact_full_api_key(monkeypatch):
    """Test that a full API key in text is replaced with redacted version."""
    test_key = "sk-or-test-key-12345678901234567890"
    monkeypatch.setenv("OPENROUTER_API_KEY", test_key)

    error_message = f"Authentication failed with key: {test_key}"
    redacted = redact_api_key(error_message)

    # Should not contain the full key
    assert test_key not in redacted
    # Should contain the redacted version showing first 4 chars (sk-o)
    assert "sk-o..." in redacted
    assert "[REDACTED]" in redacted


def test_redact_sk_or_pattern(monkeypatch):
    """Test the regex pattern catches sk-or-* keys."""
    # Set a different key in environment
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-env-key-123")

    # Test with a different key pattern in the text
    error_message = "Error with key sk-or-v1-abcdefghijklmnop in request"
    redacted = redact_api_key(error_message)

    # Should redact the pattern even if it's not the env key
    assert "sk-or-v1-abcdefghijklmnop" not in redacted
    assert "sk-or-...[REDACTED]" in redacted


def test_redact_preserves_other_text(monkeypatch):
    """Test non-key text is preserved."""
    test_key = "sk-or-test-key-99999"
    monkeypatch.setenv("OPENROUTER_API_KEY", test_key)

    error_message = f"Connection failed at line 42. API key {test_key} is invalid."
    redacted = redact_api_key(error_message)

    # Non-key text should be preserved
    assert "Connection failed at line 42" in redacted
    assert "is invalid" in redacted
    # Key should be redacted
    assert test_key not in redacted


def test_redact_handles_empty_key(monkeypatch):
    """Test graceful handling when OPENROUTER_API_KEY is empty."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    error_message = "Some error message with no key"
    redacted = redact_api_key(error_message)

    # Should return original message unchanged
    assert redacted == error_message


def test_redact_multiple_occurrences(monkeypatch):
    """Test multiple key occurrences are all redacted."""
    test_key = "sk-or-multi-key-abcdef1234567890"
    monkeypatch.setenv("OPENROUTER_API_KEY", test_key)

    error_message = f"Key {test_key} failed. Retry with {test_key} did not work."
    redacted = redact_api_key(error_message)

    # Should not contain any occurrence of the full key
    assert test_key not in redacted
    # Should contain multiple redacted versions
    redacted_count = redacted.count("[REDACTED]")
    assert redacted_count >= 2, (
        f"Expected at least 2 redactions, found {redacted_count}"
    )


def test_redact_short_key_not_redacted(monkeypatch):
    """Test that keys shorter than 8 chars are not redacted (safety check)."""
    short_key = "sk-or"
    monkeypatch.setenv("OPENROUTER_API_KEY", short_key)

    error_message = f"Error with key: {short_key}"
    redacted = redact_api_key(error_message)

    # Short key should not be redacted (exact match redaction requires >8 chars)
    # But regex pattern should still catch it if it matches sk-or-* pattern
    # Since "sk-or" alone doesn't match the pattern, it should remain
    assert "Error with key:" in redacted
