"""Tests for retry decorator functionality."""

from unittest.mock import patch

import pytest

from src.generate_changelog import retry_api_call


# Mock time.sleep to make tests instant
@pytest.fixture(autouse=True)
def mock_sleep():
    """Mock time.sleep to make tests run instantly."""
    with patch("time.sleep") as mock:
        yield mock


def test_retry_success_first_attempt():
    """Test successful API call on first attempt."""

    @retry_api_call(max_retries=3)
    def successful_call():
        return "success"

    result = successful_call()
    assert result == "success"


def test_retry_rate_limit_429_then_success():
    """Test retry on 429 rate limit error, then success."""
    call_count = 0

    @retry_api_call(max_retries=3, delay=1)
    def rate_limited_call():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Error 429: Too many requests - rate limit exceeded")
        return "success after retry"

    result = rate_limited_call()
    assert result == "success after retry"
    assert call_count == 2


def test_retry_rate_limit_exhaustion():
    """Test that rate limit exhaustion raises exception."""

    @retry_api_call(max_retries=3, delay=1)
    def always_rate_limited():
        raise Exception("429 Rate limit exceeded")

    with pytest.raises(Exception) as exc_info:
        always_rate_limited()

    assert "Rate limit exceeded" in str(exc_info.value)


def test_retry_auth_error_401_no_retry():
    """Test that 401 auth errors fail immediately without retry."""
    call_count = 0

    @retry_api_call(max_retries=3)
    def auth_error():
        nonlocal call_count
        call_count += 1
        raise Exception("401 Unauthorized: Invalid API key")

    with pytest.raises(Exception) as exc_info:
        auth_error()

    # Should fail immediately without retrying
    assert call_count == 1
    assert "Authentication error" in str(exc_info.value)


def test_retry_model_not_found_404_no_retry():
    """Test that 404 model not found errors fail immediately without retry."""
    call_count = 0

    @retry_api_call(max_retries=3)
    def model_not_found():
        nonlocal call_count
        call_count += 1
        raise Exception("404 Model not found: openai/gpt-99-ultra")

    with pytest.raises(Exception) as exc_info:
        model_not_found()

    # Should fail immediately without retrying
    assert call_count == 1
    assert "Model availability error" in str(exc_info.value)


def test_retry_payload_too_large_413():
    """Test that 413 payload too large errors are handled correctly."""
    call_count = 0

    @retry_api_call(max_retries=3)
    def payload_too_large():
        nonlocal call_count
        call_count += 1
        raise Exception("413 Request Entity Too Large")

    with pytest.raises(Exception) as exc_info:
        payload_too_large()

    # Should fail immediately without retrying (architectural error)
    assert call_count == 1
    assert "Payload too large error" in str(exc_info.value)


def test_retry_timeout_then_success():
    """Test retry on timeout error, then success."""
    call_count = 0

    @retry_api_call(max_retries=3, delay=1)
    def timeout_then_success():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Connection timeout after 30 seconds")
        return "success after timeout"

    result = timeout_then_success()
    assert result == "success after timeout"
    assert call_count == 2


def test_retry_network_error_exhaustion():
    """Test network error retry exhaustion."""
    call_count = 0

    @retry_api_call(max_retries=3, delay=1)
    def always_network_error():
        nonlocal call_count
        call_count += 1
        raise Exception("Network connection failed")

    with pytest.raises(Exception) as exc_info:
        always_network_error()

    # Should retry all attempts before failing
    assert call_count == 3
    assert "Network error" in str(exc_info.value)


def test_retry_generic_error_then_success():
    """Test retry on generic error, then success."""
    call_count = 0

    @retry_api_call(max_retries=3, delay=1)
    def generic_error_then_success():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Some random API error")
        return "success after generic error"

    result = generic_error_then_success()
    assert result == "success after generic error"
    assert call_count == 2


def test_retry_returns_none_when_all_succeed_without_return():
    """Test that decorator returns None if function doesn't return anything."""

    @retry_api_call(max_retries=3)
    def void_function():
        pass

    result = void_function()
    assert result is None


def test_retry_with_multiple_error_types():
    """Test retry behavior with different error types in sequence."""
    call_count = 0

    @retry_api_call(max_retries=5, delay=1)
    def mixed_errors():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Network connection error")
        elif call_count == 2:
            raise Exception("Timeout waiting for response")
        elif call_count == 3:
            return "success after multiple retries"

    result = mixed_errors()
    assert result == "success after multiple retries"
    assert call_count == 3


def test_retry_generic_error_exhaustion_returns_none():
    """Test that exhausting all retries on generic errors returns None."""
    call_count = 0

    @retry_api_call(max_retries=3, delay=1)
    def always_generic_error():
        nonlocal call_count
        call_count += 1
        raise Exception("Some unknown server error")

    with pytest.raises(Exception) as exc_info:
        always_generic_error()

    assert "unknown server error" in str(exc_info.value)
    # Should have retried all attempts
    assert call_count == 3


def test_retry_generic_error_final_attempt_guidance(capfd):
    """Test that final attempt failure prints guidance messages."""

    @retry_api_call(max_retries=2, delay=1)
    def always_fails():
        raise Exception("Some persistent error")

    with pytest.raises(Exception) as exc_info:
        always_fails()

    assert "persistent error" in str(exc_info.value)
    captured = capfd.readouterr()
    assert "Final attempt failed" in captured.out
    assert "Reducing the days_back parameter" in captured.out
    assert "Using a different model" in captured.out
    assert "Checking OpenRouter service status" in captured.out


def test_retry_preserves_function_name():
    """Test that decorator preserves function name and docstring."""

    @retry_api_call(max_retries=3)
    def my_function():
        """This is my function."""
        return "result"

    assert my_function.__name__ == "my_function"
    assert my_function.__doc__ == "This is my function."
