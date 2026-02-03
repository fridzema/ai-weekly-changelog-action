"""Shared pytest fixtures and configuration for all tests."""

import os
from unittest.mock import Mock

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up required environment variables before any module imports.

    This fixture runs once at the session start and ensures all required
    environment variables are set before src.generate_changelog is imported
    in any test file.
    """
    os.environ["OPENROUTER_API_KEY"] = "sk-or-test-key-abcdef123456"
    os.environ["GITHUB_REPOSITORY"] = "test-org/test-repo"
    os.environ["MODEL"] = "openai/gpt-5-mini"
    os.environ["OUTPUT_LANGUAGE"] = "English"
    os.environ["FORCE_UPDATE"] = "false"
    os.environ["EXTENDED_ANALYSIS"] = "false"
    os.environ["DRY_RUN"] = "false"
    os.environ["DAYS_BACK"] = "7"


@pytest.fixture
def sample_commits():
    """Return a list of formatted commit strings for testing."""
    return [
        "abc123|feat: Add new feature|Author1|2024-01-01|abc",
        "def456|fix: Fix critical bug|Author2|2024-01-02|def",
        "ghi789|docs: Update README|Author3|2024-01-03|ghi",
    ]


@pytest.fixture
def sample_commits_raw():
    """Return raw commits.txt content (newline-separated)."""
    return """abc123|feat: Add new feature|Author1|2024-01-01|abc
def456|fix: Fix critical bug|Author2|2024-01-02|def
ghi789|docs: Update README|Author3|2024-01-03|ghi
"""


@pytest.fixture
def mock_openai_response():
    """Return a Mock object mimicking OpenAI API response structure."""
    response = Mock()
    response.choices = [Mock()]
    response.choices[0].message = Mock()
    response.choices[0].message.content = "### Technical Summary\nTest content"
    return response


@pytest.fixture
def clean_files(tmp_path, monkeypatch):
    """Provide isolated temporary directory for file testing.

    Args:
        tmp_path: pytest's built-in temporary directory fixture
        monkeypatch: pytest's monkeypatch fixture for changing working directory

    Yields:
        Path: Temporary directory path
    """
    monkeypatch.chdir(tmp_path)
    yield tmp_path
