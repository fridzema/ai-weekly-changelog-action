# Test Architecture for Python GitHub Action

**Project:** ai-weekly-changelog-action
**Domain:** Python GitHub Action Testing
**Researched:** 2026-02-03
**Confidence:** HIGH

## Recommended Test Architecture

### Project Structure (src Layout)

```
ai-weekly-changelog-action/
├── pyproject.toml           # Configuration hub
├── src/
│   └── generate_changelog.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Shared fixtures
│   ├── test_retry_logic.py
│   ├── test_chunking.py
│   ├── test_changelog_writing.py
│   ├── test_language_config.py
│   ├── test_integration.py
│   └── fixtures/
│       ├── __init__.py
│       ├── api_responses.py  # Mock OpenAI responses
│       └── sample_data.py    # Sample commits/changelog data
├── action.yml
└── requirements.txt
```

**Rationale:** The src layout is the pytest-recommended approach for new test implementations. It ensures tests run against the installed version of code, preventing import issues and accidental testing of uninstalled modules.

**Reference:** [pytest Good Integration Practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html) (HIGH confidence - official docs)

## Component Boundaries

| Component | Responsibility | Test Strategy |
|-----------|---------------|---------------|
| **retry_api_call decorator** | API call retrying with exponential backoff | Unit tests with mocked exceptions |
| **OpenAI client interaction** | Chat completion calls via OpenRouter | Integration tests with mocked API |
| **Chunking algorithm** | Splitting large commit sets (>5 commits) | Unit tests with various commit counts |
| **Changelog file writing** | File I/O, markdown formatting | Unit tests with tmp_path fixture |
| **Language configuration** | Multi-language support (5 languages) | Parametrized tests for each language |
| **Environment handling** | Reading env vars, validation | Unit tests with monkeypatch |
| **Commit processing** | Parsing, formatting, linking | Unit tests with sample data |

## Test Organization

### 1. Unit Tests (Primary Focus)

**Tests per module:**

```python
# tests/test_retry_logic.py
"""Tests for retry_api_call decorator with various failure scenarios"""

# tests/test_chunking.py
"""Tests for generate_chunked_summary and chunk merging logic"""

# tests/test_changelog_writing.py
"""Tests for changelog file operations and markdown formatting"""

# tests/test_language_config.py
"""Tests for multi-language configuration and date formatting"""

# tests/test_commit_processing.py
"""Tests for commit parsing, formatting, and link generation"""
```

**Organization principle:** One test file per major function or logical grouping. Mirror the structure of functionality, not file structure.

### 2. Integration Tests (Secondary)

```python
# tests/test_integration.py
"""End-to-end tests with mocked OpenAI but real file I/O"""
```

Test complete flows: commits.txt → API calls → CHANGELOG.md output

### 3. Fixture Organization

```python
# tests/conftest.py - Global fixtures
"""
- mock_openai_client: Configured OpenAI client mock
- sample_commits: Standard set of test commits
- clean_environment: Reset env vars between tests
"""

# tests/fixtures/api_responses.py
"""
- Technical and business summary response fixtures
- Error response fixtures (401, 429, 404, timeout)
- Chunk merge response fixtures
"""

# tests/fixtures/sample_data.py
"""
- Sample commit data in various formats
- Expected changelog outputs
- Language-specific test data
"""
```

**conftest.py strategy:** Global fixtures only. Specific fixtures in dedicated modules, imported explicitly when needed for clarity.

**Reference:** [pytest fixtures documentation](https://docs.pytest.org/en/stable/how-to/fixtures.html) (HIGH confidence)

## Patterns to Follow

### Pattern 1: Mocking OpenAI API Responses

**What:** Use the `openai-responses` pytest plugin for simple mocking, or manual Pydantic model construction for complex scenarios.

**When:** Any test that would call `client.chat.completions.create()`

**Example using openai-responses (Recommended for simplicity):**
```python
import pytest
import openai_responses
from openai import OpenAI

@openai_responses.mock()
def test_technical_summary_generation(sample_commits):
    """Test technical summary generation with mocked OpenAI"""
    client = OpenAI(api_key="sk-fake-test-key")

    # openai-responses automatically mocks the API
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Generate summary"}]
    )

    assert response.choices[0].message.content
```

**Example with manual mocking (For complex scenarios):**
```python
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice

@pytest.fixture
def mock_openai_completion(monkeypatch):
    """Mock OpenAI ChatCompletion with custom response"""
    def mock_create(*args, **kwargs):
        return ChatCompletion(
            id="test-completion",
            object="chat.completion",
            created=1234567890,
            model="gpt-4",
            choices=[
                Choice(
                    index=0,
                    message=ChatCompletionMessage(
                        role="assistant",
                        content="## Technical Summary\n- Feature A added\n- Bug B fixed"
                    ),
                    finish_reason="stop"
                )
            ]
        )

    monkeypatch.setattr("openai.resources.chat.completions.Completions.create", mock_create)
    return mock_create
```

**Reference:**
- [openai-responses PyPI](https://pypi.org/project/openai-responses/) (HIGH confidence - official plugin)
- [Mocking OpenAI API Guide](https://tobiaslang.medium.com/mocking-the-openai-api-in-python-a-step-by-step-guide-4630efcb809d) (MEDIUM confidence - verified pattern)

### Pattern 2: Testing Retry Logic with Controlled Failures

**What:** Test the `retry_api_call` decorator by forcing controlled failures, then success.

**When:** Testing any decorated function that should retry on specific errors.

**Example:**
```python
import pytest
from unittest.mock import Mock, call

def test_retry_on_rate_limit(monkeypatch, capsys):
    """Test retry logic handles 429 rate limiting correctly"""
    mock_func = Mock()

    # Simulate: fail twice with 429, then succeed
    mock_func.side_effect = [
        Exception("429: Rate limit exceeded"),
        Exception("429: Too many requests"),
        "success"
    ]

    @retry_api_call(max_retries=3, delay=0.1)
    def api_function():
        return mock_func()

    result = api_function()

    assert result == "success"
    assert mock_func.call_count == 3

    captured = capsys.readouterr()
    assert "Rate limit hit" in captured.out
    assert "attempt 1/3" in captured.out

def test_retry_exhaustion_on_auth_error(monkeypatch):
    """Test retry logic fails fast on auth errors (401)"""
    mock_func = Mock(side_effect=Exception("401: Unauthorized"))

    @retry_api_call(max_retries=3, delay=0.1)
    def api_function():
        return mock_func()

    with pytest.raises(Exception, match="Authentication error"):
        api_function()

    # Should fail immediately, not retry
    assert mock_func.call_count == 1
```

**Why this works:** The decorator uses exception message matching to determine retry strategy. Tests verify correct backoff and fast-fail behavior.

### Pattern 3: File I/O Testing with tmp_path

**What:** Use pytest's built-in `tmp_path` fixture for isolated, automatically cleaned-up file operations.

**When:** Testing changelog writing, commit file reading, or any file I/O.

**Example:**
```python
def test_changelog_creation(tmp_path):
    """Test creating a new changelog file"""
    changelog_path = tmp_path / "CHANGELOG.md"

    # Simulate writing changelog
    write_changelog_entry(
        changelog_path,
        week=5,
        year=2026,
        commits=["feat: add feature", "fix: resolve bug"],
        tech_summary="Technical changes...",
        business_summary="User impact..."
    )

    # Verify file created and formatted correctly
    assert changelog_path.exists()
    content = changelog_path.read_text(encoding="utf-8")

    assert "## Week 5, 2026" in content
    assert "Technical changes..." in content
    assert "User impact..." in content

def test_changelog_force_update(tmp_path):
    """Test force updating existing changelog entry"""
    changelog_path = tmp_path / "CHANGELOG.md"

    # Create existing entry
    changelog_path.write_text("# Changelog\n\n## Week 5, 2026\nOld content\n")

    # Force update
    write_changelog_entry(
        changelog_path,
        week=5,
        year=2026,
        commits=["feat: new feature"],
        tech_summary="Updated content",
        business_summary="New impact",
        force=True
    )

    content = changelog_path.read_text(encoding="utf-8")
    assert "Old content" not in content
    assert "Updated content" in content
```

**Reference:** [pytest tmp_path documentation](https://docs.pytest.org/en/stable/how-to/tmp_path.html) (HIGH confidence - official docs)

### Pattern 4: Environment Variable Mocking

**What:** Use `monkeypatch` fixture to safely set/unset environment variables for test isolation.

**When:** Testing code that reads from `os.getenv()` or requires specific environment configuration.

**Example:**
```python
def test_api_key_validation_missing(monkeypatch):
    """Test that missing API key causes proper error"""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(SystemExit) as exc_info:
        # Code that validates API key on import
        import importlib
        importlib.reload(generate_changelog)

    assert exc_info.value.code == 1

def test_api_key_validation_invalid_format(monkeypatch, capsys):
    """Test warning for invalid API key format"""
    monkeypatch.setenv("OPENROUTER_API_KEY", "invalid-key-format")

    import importlib
    importlib.reload(generate_changelog)

    captured = capsys.readouterr()
    assert "doesn't match expected OpenRouter format" in captured.out

def test_language_configuration(monkeypatch):
    """Test language config selection"""
    monkeypatch.setenv("OUTPUT_LANGUAGE", "Dutch")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test-key")

    # Test would reload module and verify Dutch config is used
    # ... test language-specific behavior
```

**Reference:** [pytest monkeypatch documentation](https://docs.pytest.org/en/stable/how-to/monkeypatch.html) (HIGH confidence - official docs)

### Pattern 5: Parametrized Tests for Multi-Language Support

**What:** Use `@pytest.mark.parametrize` to test all 5 supported languages without code duplication.

**When:** Testing language-specific behavior like date formatting, labels, fallback messages.

**Example:**
```python
@pytest.mark.parametrize("language,expected_label,date_format", [
    ("English", "Week", "%m-%d-%Y"),
    ("Dutch", "Week", "%d-%m-%Y"),
    ("German", "Woche", "%d.%m.%Y"),
    ("French", "Semaine", "%d/%m/%Y"),
    ("Spanish", "Semana", "%d/%m/%Y"),
])
def test_language_date_formatting(language, expected_label, date_format, monkeypatch):
    """Test date formatting for each supported language"""
    monkeypatch.setenv("OUTPUT_LANGUAGE", language)

    config = get_language_config(language)

    assert config["week_label"] == expected_label

    # Test date formatting
    test_date = datetime.date(2026, 2, 3)
    formatted = test_date.strftime(date_format)

    if language == "English":
        assert formatted == "02-03-2026"
    elif language == "Dutch":
        assert formatted == "03-02-2026"
    elif language == "German":
        assert formatted == "03.02.2026"

@pytest.mark.parametrize("language", ["English", "Dutch", "German", "French", "Spanish"])
def test_fallback_messages(language, monkeypatch):
    """Test fallback messages exist for all languages"""
    monkeypatch.setenv("OUTPUT_LANGUAGE", language)

    config = get_language_config(language)

    assert config["fallback_tech"]
    assert config["fallback_business"]
    assert len(config["fallback_tech"]) > 20  # Meaningful message
```

**Reference:** [pytest parametrize documentation](https://docs.pytest.org/en/stable/how-to/parametrize.html) (HIGH confidence - official docs)

### Pattern 6: Testing Chunking Algorithm

**What:** Test the intelligent chunking system that splits large commit sets into 5-commit chunks.

**When:** Testing `generate_chunked_summary`, `merge_chunk_summaries`, and chunk detection logic.

**Example:**
```python
def test_no_chunking_for_small_sets():
    """Test that small commit sets (≤5) don't trigger chunking"""
    commits = ["commit1", "commit2", "commit3", "commit4", "commit5"]

    # Mock the single API call
    with patch('generate_summary') as mock_generate:
        mock_generate.return_value = "Summary for all commits"

        result = generate_chunked_summary(
            commits,
            tech_prompt_template,
            "test summary",
            "technical"
        )

        # Should call generate_summary once, not use chunking
        assert mock_generate.call_count == 1
        assert "Summary for all commits" in result

def test_chunking_for_large_sets():
    """Test chunking triggers for >5 commits and merges correctly"""
    commits = [f"commit{i}" for i in range(15)]  # 15 commits = 3 chunks

    with patch('generate_summary') as mock_generate, \
         patch('merge_chunk_summaries') as mock_merge:

        # Each chunk gets a summary
        mock_generate.side_effect = [
            "Chunk 1 summary",
            "Chunk 2 summary",
            "Chunk 3 summary"
        ]
        mock_merge.return_value = "Merged comprehensive summary"

        result = generate_chunked_summary(
            commits,
            tech_prompt_template,
            "test summary",
            "technical"
        )

        # Verify chunking behavior
        assert mock_generate.call_count == 3
        assert mock_merge.call_count == 1
        assert result == "Merged comprehensive summary"

        # Verify merge was called with correct args
        merge_call_args = mock_merge.call_args
        assert len(merge_call_args[0][0]) == 3  # 3 chunk summaries
        assert merge_call_args[0][1] == "technical"
        assert merge_call_args[0][2] == 15  # total commits

def test_chunking_resilience():
    """Test chunking continues even if individual chunks fail"""
    commits = [f"commit{i}" for i in range(10)]  # 2 chunks

    with patch('generate_summary') as mock_generate, \
         patch('merge_chunk_summaries') as mock_merge:

        # Chunk 1 succeeds, chunk 2 fails
        mock_generate.side_effect = [
            "Chunk 1 summary",
            Exception("API error")
        ]
        mock_merge.return_value = "Partial merged summary"

        result = generate_chunked_summary(
            commits,
            tech_prompt_template,
            "test summary",
            "technical"
        )

        # Should still complete with partial results
        assert mock_merge.call_count == 1
        merge_chunks = mock_merge.call_args[0][0]
        assert "Chunk 1 summary" in merge_chunks[0]
        assert "analysis failed" in merge_chunks[1]
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Testing with Real API Calls

**What:** Making actual OpenAI/OpenRouter API calls in tests.

**Why bad:**
- Costs money (API usage charges)
- Slow test execution
- Requires network connectivity
- Non-deterministic results
- Uses rate limit quota

**Instead:** Always mock API responses using `openai-responses` plugin or manual mocks. Reserve real API calls for manual integration testing only.

### Anti-Pattern 2: Shared Mutable Test State

**What:** Reusing the same fixture data that gets modified by tests.

**Why bad:**
- Tests affect each other
- Non-deterministic failures based on test execution order
- Hard to debug

**Instead:** Use fixture factories or `scope="function"` (default) to ensure test isolation.

```python
# BAD: Shared mutable state
@pytest.fixture
def sample_commits():
    return ["commit1", "commit2"]  # Gets modified by tests

# GOOD: Factory pattern
@pytest.fixture
def sample_commits():
    def _make_commits(count=5):
        return [f"feat: feature {i}" for i in range(count)]
    return _make_commits

def test_something(sample_commits):
    commits = sample_commits(count=10)
    # Modify commits safely, no impact on other tests
```

### Anti-Pattern 3: Not Cleaning Up Environment Variables

**What:** Setting environment variables without cleanup between tests.

**Why bad:**
- Tests leak state to subsequent tests
- Hard-to-debug failures when test order changes

**Instead:** Always use `monkeypatch` fixture (automatic cleanup) or explicit teardown.

```python
# BAD: Manual os.environ modification
def test_something():
    os.environ["MODEL"] = "test-model"
    # ... test code
    # Cleanup forgotten!

# GOOD: monkeypatch with automatic cleanup
def test_something(monkeypatch):
    monkeypatch.setenv("MODEL", "test-model")
    # ... test code
    # Automatic cleanup after test
```

### Anti-Pattern 4: Over-Mocking Internal Logic

**What:** Mocking so much internal behavior that you're testing the mocks, not the code.

**Why bad:**
- Tests become brittle and break on refactoring
- False confidence (tests pass but code broken)
- Doesn't catch integration issues

**Instead:** Mock external dependencies (API calls, file system for unit tests), but test real logic.

```python
# BAD: Over-mocking
def test_changelog_generation(monkeypatch):
    monkeypatch.setattr("module.format_commits", lambda x: "mocked")
    monkeypatch.setattr("module.generate_summary", lambda x: "mocked")
    monkeypatch.setattr("module.write_file", lambda x: None)
    # Test does nothing meaningful

# GOOD: Mock only external boundary
@openai_responses.mock()
def test_changelog_generation(tmp_path):
    # Real commit formatting
    # Real changelog writing
    # Only API call is mocked
    result = generate_changelog(tmp_path / "CHANGELOG.md", commits_data)
    assert result  # Test real behavior
```

### Anti-Pattern 5: Not Testing Error Paths

**What:** Only testing the "happy path" where everything works.

**Why bad:**
- Production code encounters errors constantly
- Error handling often has bugs
- User-facing error messages may be unhelpful

**Instead:** Explicitly test error conditions, especially those with custom handling.

```python
def test_rate_limit_error_guidance(capsys):
    """Test that rate limiting provides helpful user guidance"""
    # ... setup to trigger 429 error

    captured = capsys.readouterr()
    assert "Rate limit exceeded" in captured.out
    assert "Try again in a few minutes" in captured.out
    assert "different model" in captured.out

def test_auth_error_guidance(capsys):
    """Test that auth errors provide actionable steps"""
    # ... setup to trigger 401 error

    captured = capsys.readouterr()
    assert "check your OPENROUTER_API_KEY" in captured.out
    assert "https://openrouter.ai/keys" in captured.out
```

## Configuration Management

### pyproject.toml Configuration

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "ai-weekly-changelog-action"
version = "1.0.0"
dependencies = [
    "openai>=1.14,<2",
    "requests",
]

[project.optional-dependencies]
test = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "pytest-mock>=3.12",
    "openai-responses>=0.8",  # For OpenAI API mocking
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-report=html",
    "--cov-report=xml",
    "--import-mode=importlib",
    "--strict-markers",
    "-v"
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
]

[tool.coverage.run]
source = ["src"]
branch = true
omit = [
    "tests/*",
    "**/conftest.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "raise AssertionError",
    "raise NotImplementedError",
]
precision = 2
fail_under = 80  # Minimum 80% coverage required

[tool.coverage.html]
directory = "htmlcov"
```

**Reference:**
- [pytest-cov configuration](https://pytest-cov.readthedocs.io/en/latest/config.html) (HIGH confidence)
- [Coverage.py configuration](https://coverage.readthedocs.io/en/latest/config.html) (HIGH confidence)

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[test]"

    - name: Run tests with coverage
      run: |
        pytest --cov --cov-report=xml --cov-report=term

    - name: Upload coverage reports
      uses: codecov/codecov-action@v4
      if: matrix.python-version == '3.11'
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

**Reference:** [GitHub Actions: Building and testing Python](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python) (HIGH confidence - official docs)

## Coverage Strategy

### Coverage Targets

| Component | Target Coverage | Priority |
|-----------|----------------|----------|
| Core logic (retry, chunking) | 95%+ | Critical |
| API interaction | 90%+ | High |
| File I/O operations | 90%+ | High |
| Configuration/language | 85%+ | Medium |
| Error handling | 100% | Critical |
| CLI/main execution | 70%+ | Low |

### Measuring Coverage

```bash
# Run tests with coverage report
pytest --cov=src --cov-report=term-missing

# Generate HTML report for detailed view
pytest --cov=src --cov-report=html

# Fail if coverage drops below threshold
pytest --cov=src --cov-fail-under=80
```

### Coverage Exclusions

Exclude from coverage:
- `if __name__ == "__main__"` blocks
- Defensive assertions that should never trigger
- Type checking blocks (`if TYPE_CHECKING`)
- Abstract methods meant to be overridden

Use `# pragma: no cover` sparingly and with justification.

## Test Execution Strategy

### Local Development

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_retry_logic.py

# Run tests matching pattern
pytest -k "test_retry"

# Run with verbose output
pytest -v

# Stop on first failure (fast feedback)
pytest -x

# Run only failed tests from last run
pytest --lf

# Show print statements
pytest -s
```

### CI/CD Pipeline

```bash
# Full test suite with coverage
pytest --cov=src --cov-report=xml --cov-report=term-missing

# Run in parallel (for larger test suites)
pytest -n auto  # Requires pytest-xdist

# Run with specific markers
pytest -m "not slow"  # Skip slow integration tests in CI
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-check
        name: pytest-check
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
        args: ["-x", "--tb=short"]
```

## Test Data Management

### Fixture Organization Strategy

```python
# tests/fixtures/api_responses.py
"""Reusable OpenAI API response fixtures"""

TECHNICAL_SUMMARY_RESPONSE = """
### Technical Changelog Summary
Development activity focused on testing infrastructure.

#### Main Changes by Category

**Features:**
- Added comprehensive test suite with pytest
- Implemented API mocking with openai-responses

**Testing:**
- Created fixtures for common test scenarios
- Added parametrized tests for multi-language support
"""

BUSINESS_SUMMARY_RESPONSE = """
### Summary of Recent Updates
This week focused on improving code quality through comprehensive testing.

#### User Experience Impact
- More reliable changelog generation
- Better error handling and user guidance

#### Business Benefits
- Reduced bug risk through automated testing
- Faster development cycles with quick feedback
"""

ERROR_RESPONSES = {
    "rate_limit": "429: Rate limit exceeded",
    "auth_error": "401: Unauthorized - Invalid API key",
    "model_not_found": "404: Model not found or not available",
    "network_timeout": "Connection timeout after 30s",
}
```

```python
# tests/fixtures/sample_data.py
"""Sample test data for commits and changelogs"""

SAMPLE_COMMITS = [
    "feat: add retry logic with exponential backoff",
    "fix: resolve changelog duplication issue",
    "docs: update README with testing instructions",
    "refactor: extract language config to separate module",
    "test: add unit tests for chunking algorithm",
]

SAMPLE_COMMITS_RAW = """
abc123|feat: add retry logic|Alice|2026-02-01|abc
def456|fix: resolve changelog duplication|Bob|2026-02-02|def
ghi789|docs: update README|Alice|2026-02-03|ghi
"""

EXPECTED_CHANGELOG_ENTRY = """
## Week 5, 2026

*Generated on 02-03-2026 - 3 commits*

### 🔧 Technical Changes
{technical_summary}

### 📈 User Impact
{business_summary}

### 📋 All Commits
- [abc](https://github.com/owner/repo/commit/abc123) feat: add retry logic - Alice
- [def](https://github.com/owner/repo/commit/def456) fix: resolve changelog duplication - Bob
- [ghi](https://github.com/owner/repo/commit/ghi789) docs: update README - Alice

---
"""
```

## Testing Checklist for Implementation

### Phase 1: Foundation (Week 1)
- [ ] Set up pytest with pyproject.toml configuration
- [ ] Create tests/ directory structure with conftest.py
- [ ] Install test dependencies (pytest, pytest-cov, openai-responses, pytest-mock)
- [ ] Configure coverage reporting (80% minimum)
- [ ] Set up GitHub Actions workflow for CI

### Phase 2: Core Logic Tests (Week 2)
- [ ] Test retry_api_call decorator with various error types
- [ ] Test exponential backoff timing and jitter
- [ ] Test fast-fail on auth errors (401)
- [ ] Test rate limit handling (429)
- [ ] Test network error retries

### Phase 3: Chunking & API Tests (Week 3)
- [ ] Test chunking detection (≤5 vs >5 commits)
- [ ] Test chunk creation and boundaries
- [ ] Test merge_chunk_summaries functionality
- [ ] Test OpenAI client interaction with mocked responses
- [ ] Test chunk failure resilience

### Phase 4: File I/O Tests (Week 4)
- [ ] Test changelog creation (new file)
- [ ] Test changelog updates (existing file)
- [ ] Test force update mode
- [ ] Test duplicate entry prevention
- [ ] Test markdown formatting

### Phase 5: Configuration Tests (Week 5)
- [ ] Test environment variable handling (monkeypatch)
- [ ] Test language configuration for all 5 languages (parametrized)
- [ ] Test date formatting per language
- [ ] Test API key validation
- [ ] Test fallback messages

### Phase 6: Integration & Polish (Week 6)
- [ ] Integration tests for complete flow
- [ ] Error path testing and user guidance
- [ ] Coverage analysis and gap filling
- [ ] Documentation of test patterns
- [ ] Pre-commit hook setup

## Sources

### Official Documentation (HIGH Confidence)
- [pytest Good Integration Practices](https://docs.pytest.org/en/stable/explanation/goodpractices.html)
- [pytest fixtures documentation](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [pytest tmp_path documentation](https://docs.pytest.org/en/stable/how-to/tmp_path.html)
- [pytest monkeypatch documentation](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)
- [pytest parametrize documentation](https://docs.pytest.org/en/stable/how-to/parametrize.html)
- [pytest-cov configuration](https://pytest-cov.readthedocs.io/en/latest/config.html)
- [Coverage.py configuration](https://coverage.readthedocs.io/en/latest/config.html)
- [GitHub Actions: Building and testing Python](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)

### Tools & Plugins (HIGH Confidence)
- [openai-responses PyPI](https://pypi.org/project/openai-responses/)
- [pytest-retry PyPI](https://pypi.org/project/pytest-retry/)

### Guides & Tutorials (MEDIUM Confidence - Verified Patterns)
- [Mocking OpenAI API Guide](https://tobiaslang.medium.com/mocking-the-openai-api-in-python-a-step-by-step-guide-4630efcb809d)
- [Automated Python Unit Testing with Pytest and GitHub Actions](https://pytest-with-eric.com/integrations/pytest-github-actions/)
- [Pytest Best Practices: Organizing Tests](https://pytest-with-eric.com/pytest-best-practices/pytest-organize-tests/)
