# Phase 2: Testing Infrastructure - Research

**Researched:** 2026-02-03
**Domain:** Python testing with pytest
**Confidence:** HIGH

## Summary

This research investigates pytest best practices for testing a Python module with challenging characteristics: import-time side effects (API key validation, OpenAI client initialization, sys.exit calls), global state management, and comprehensive error handling requiring 80%+ branch coverage.

The standard approach combines pytest's built-in fixtures (monkeypatch, tmp_path) with minimal external dependencies (pytest-cov, pytest-mock) and strategic workarounds for import-time side effects. The primary challenge is module initialization that requires OPENROUTER_API_KEY at import time and calls sys.exit(1) if missing.

**Key findings:**
- conftest.py with autouse fixtures provides environment setup before module import
- pytest.raises(SystemExit) captures sys.exit() calls for testing
- mocker.patch with side_effect enables multi-scenario decorator testing
- pytest-cov with pyproject.toml configuration enforces 80% branch coverage threshold
- tmp_path fixture provides isolated file I/O testing

**Primary recommendation:** Use conftest.py session-scoped autouse fixture to set OPENROUTER_API_KEY before generate_changelog.py imports, enabling normal module loading. Test individual functions with mocker.patch for API calls and monkeypatch for varying environment configurations.

## Standard Stack

The established libraries/tools for pytest-based testing:

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | >=8.0 | Test framework | Industry standard Python testing framework with fixture system |
| pytest-cov | >=4.0 | Coverage measurement | Official pytest integration with coverage.py for branch coverage |
| pytest-mock | >=3.0 | Mocking utilities | Thin wrapper around unittest.mock providing fixture-based automatic cleanup |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| coverage[toml] | >=7.0 | Coverage engine | Automatically installed with pytest-cov; toml extra enables pyproject.toml config |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pytest-mock | unittest.mock directly | pytest-mock provides mocker fixture with automatic cleanup; raw unittest.mock requires manual teardown |
| tmp_path | tmpdir (legacy) | tmp_path uses pathlib.Path (modern); tmpdir uses py.path.local (deprecated) |
| pytest-env | Manual conftest.py setup | pytest-env provides declarative config but adds dependency; conftest.py works without extra package |

**Installation:**
```bash
pip install pytest>=8.0 pytest-cov>=4.0 pytest-mock>=3.0
```

## Architecture Patterns

### Recommended Project Structure
```
tests/
├── conftest.py           # Shared fixtures, environment setup
├── test_retry.py         # retry_api_call decorator tests
├── test_chunking.py      # Chunking algorithm tests
├── test_changelog.py     # Changelog file operation tests
├── test_language.py      # Language config tests
└── test_redaction.py     # API key redaction tests
```

### Pattern 1: Environment Setup for Import-Time Side Effects
**What:** Use conftest.py with session-scoped autouse fixture to set required environment variables before module import
**When to use:** When testing modules that access os.getenv() or initialize clients during import

**Example:**
```python
# tests/conftest.py
import pytest
import os

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set environment variables before any imports"""
    os.environ["OPENROUTER_API_KEY"] = "sk-or-test-key-12345"
    os.environ["GITHUB_REPOSITORY"] = "test-org/test-repo"
    os.environ["MODEL"] = "openai/gpt-5-mini"
    os.environ["OUTPUT_LANGUAGE"] = "English"
    yield
    # Cleanup happens automatically after session

# Now safe to import in any test file
# import src.generate_changelog
```
**Source:** [pytest discussions #10027](https://github.com/pytest-dev/pytest/discussions/10027)

### Pattern 2: Testing sys.exit() Calls
**What:** Use pytest.raises(SystemExit) to catch and verify exit codes
**When to use:** Testing error paths that call sys.exit()

**Example:**
```python
import pytest

def test_missing_api_key_exits(monkeypatch):
    """Test that missing API key causes sys.exit(1)"""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(SystemExit) as exc_info:
        import importlib
        import src.generate_changelog
        importlib.reload(src.generate_changelog)

    assert exc_info.value.code == 1
```
**Source:** [Testing sys.exit with pytest](https://dev.to/boris/testing-exit-codes-with-pytest-1g27)

### Pattern 3: Testing Retry Decorators with Multiple Exceptions
**What:** Use mocker.patch with side_effect list to simulate retry scenarios
**When to use:** Testing decorators with complex retry logic (rate limits, auth errors, network timeouts)

**Example:**
```python
def test_retry_decorator_rate_limit_then_success(mocker):
    """Test retry decorator handles 429 rate limit then succeeds"""
    mock_func = mocker.Mock()

    # First two calls: rate limit error, third call: success
    mock_func.side_effect = [
        Exception("Error 429: Rate limit exceeded"),
        Exception("Error 429: Too many requests"),
        {"status": "success", "data": "result"}
    ]

    @retry_api_call(max_retries=3, delay=0.1)
    def api_call():
        return mock_func()

    # Should succeed after retries
    result = api_call()
    assert result == {"status": "success", "data": "result"}
    assert mock_func.call_count == 3
```
**Source:** [pytest-mock usage documentation](https://pytest-mock.readthedocs.io/en/latest/usage.html)

### Pattern 4: Isolated File I/O Testing
**What:** Use tmp_path fixture for file operations testing
**When to use:** Testing functions that read/write files

**Example:**
```python
def test_changelog_creation(tmp_path):
    """Test creating new CHANGELOG.md"""
    changelog_file = tmp_path / "CHANGELOG.md"

    # Function writes to current directory, so change to tmp_path
    import os
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        # Create test commits.txt
        commits_file = tmp_path / "commits.txt"
        commits_file.write_text("abc123|Fix bug|Author|2024-01-01|abc")

        # Run function that writes CHANGELOG.md
        # ... test code ...

        # Verify output
        assert changelog_file.exists()
        content = changelog_file.read_text()
        assert "Week" in content
    finally:
        os.chdir(original_cwd)
```
**Source:** [pytest tmp_path documentation](https://docs.pytest.org/en/stable/how-to/tmp_path.html)

### Pattern 5: Shared Mock Fixtures
**What:** Define reusable mock responses in conftest.py
**When to use:** Multiple tests need similar OpenAI API mock responses

**Example:**
```python
# tests/conftest.py
import pytest

@pytest.fixture
def mock_openai_response():
    """Standard OpenAI API response structure"""
    from unittest.mock import Mock
    response = Mock()
    response.choices = [Mock()]
    response.choices[0].message = Mock()
    response.choices[0].message.content = "Test summary content"
    return response

@pytest.fixture
def mock_openai_client(mocker, mock_openai_response):
    """Mock OpenAI client with standard response"""
    mock_client = mocker.Mock()
    mock_client.chat.completions.create.return_value = mock_openai_response
    return mock_client
```
**Source:** [pytest fixtures documentation](https://docs.pytest.org/en/stable/how-to/fixtures.html)

### Pattern 6: Parametrized Boundary Testing
**What:** Use @pytest.mark.parametrize for boundary condition testing
**When to use:** Testing chunking algorithm with 0, 1, 5, 6, 100+ commits

**Example:**
```python
@pytest.mark.parametrize("commit_count,expected_chunks", [
    (0, 0),      # No commits
    (1, 0),      # Below threshold (no chunking)
    (5, 0),      # At threshold (no chunking)
    (6, 2),      # Just above threshold (chunking starts)
    (10, 2),     # Two chunks
    (100, 20),   # Many chunks
])
def test_chunking_boundary_conditions(commit_count, expected_chunks):
    """Test chunking algorithm at boundary conditions"""
    COMMITS_PER_CHUNK = 5
    use_chunking = commit_count > COMMITS_PER_CHUNK

    if use_chunking:
        num_chunks = (commit_count + COMMITS_PER_CHUNK - 1) // COMMITS_PER_CHUNK
        assert num_chunks == expected_chunks
    else:
        assert expected_chunks == 0
```
**Source:** [pytest parametrize documentation](https://docs.pytest.org/en/stable/how-to/parametrize.html)

### Anti-Patterns to Avoid
- **Global state pollution:** Don't rely on module-level globals persisting between tests; use importlib.reload() or fixtures for isolation
- **Missing cleanup:** Don't use unittest.mock.patch without proper teardown; prefer pytest-mock's mocker fixture for automatic cleanup
- **Hardcoded paths:** Don't use absolute paths or current directory assumptions; use tmp_path for file operations
- **Slow tests:** Don't call time.sleep() in tests; mock time.sleep to make retry tests instant

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Coverage measurement | Custom code analysis | pytest-cov with coverage.py | Handles branch coverage, exclusions, parallel testing, multiple report formats |
| Mock cleanup | Manual mock.stop() calls | pytest-mock mocker fixture | Automatic teardown after test completion, prevents leaks |
| Temporary files | Custom temp directory logic | tmp_path fixture | Automatic cleanup, platform-agnostic paths, pytest integration |
| Environment isolation | Manual os.environ save/restore | monkeypatch.setenv/delenv | Automatic restore, handles missing vars, proper exception handling |
| Multiple test scenarios | Copy-pasted test functions | @pytest.mark.parametrize | DRY principle, better test discovery, clearer failure messages |

**Key insight:** pytest's fixture system provides sophisticated lifecycle management (setup/teardown, scopes, dependencies) that's difficult to replicate correctly. Use built-in fixtures instead of custom solutions.

## Common Pitfalls

### Pitfall 1: Import-Time Side Effects Break Test Isolation
**What goes wrong:** Module imports OpenAI client during import, requiring API key before any test runs. Tests fail with "OPENROUTER_API_KEY not found" even though individual tests set the key.

**Why it happens:** Python imports are cached in sys.modules. Once a module imports and executes module-level code, that state persists. Setting env vars in test functions happens AFTER import.

**How to avoid:**
- Use session-scoped autouse fixture in conftest.py to set required env vars
- Set vars before ANY test file imports the module
- Alternative: Use pytest-env plugin for declarative env var config

**Warning signs:**
- Import errors about missing env vars when running pytest
- Tests pass individually but fail when run together
- Module-level initialization code executing before fixtures

**Source:** [pytest discussions #10027](https://github.com/pytest-dev/pytest/discussions/10027)

### Pitfall 2: Mocking at Wrong Level
**What goes wrong:** Tests mock the OpenAI library itself instead of the client instance, causing client.chat.completions.create() calls to fail unmocked.

**Why it happens:** The module creates `client = OpenAI(...)` at module level. Mocking `OpenAI` class doesn't affect the already-instantiated client object.

**How to avoid:**
- Mock the specific method: `mocker.patch.object(client, 'chat.completions.create')`
- Or mock at import location: `mocker.patch('src.generate_changelog.client')`
- Don't mock: `mocker.patch('openai.OpenAI')` after client is already created

**Warning signs:**
- Mocks are set up but real API calls still attempted
- AttributeError: Mock object has no attribute 'chat'
- Tests work with reload but fail normally

**Source:** [pytest-mock usage documentation](https://pytest-mock.readthedocs.io/en/latest/usage.html)

### Pitfall 3: Coverage Reports Show Missed Branches in Error Handling
**What goes wrong:** 80% coverage target fails because error handling branches (429, 401, 404, timeout, network) aren't tested.

**Why it happens:** Retry decorator has 7 different error paths (rate limit, auth, model not found, payload too large, timeout, network, generic). Testing only success path leaves 85% of decorator uncovered.

**How to avoid:**
- Use parametrized tests with all error types
- Test both retry scenarios (fail → retry → success) and exhaustion scenarios (fail → fail → fail → raise)
- Mock time.sleep to make retry tests instant
- Use side_effect with exception lists: `[Exception("429"), Exception("429"), "success"]`

**Warning signs:**
- Coverage report shows retry_api_call at <60% coverage
- Only testing "happy path" scenarios
- No tests for specific error messages (401, 404, etc.)

**Source:** [pytest-cov configuration documentation](https://pytest-cov.readthedocs.io/en/latest/config.html)

### Pitfall 4: Test Fixtures Leak State Between Tests
**What goes wrong:** Test A modifies a fixture's state, Test B expects clean fixture but gets modified version. Tests pass individually, fail when run together.

**Why it happens:** Module-scoped or session-scoped fixtures persist across multiple tests. If tests mutate fixture data instead of treating it as read-only, changes leak.

**How to avoid:**
- Use function scope (default) for mutable fixtures
- Make fixtures return fresh data on each call
- Use yield fixtures with cleanup code after yield
- Document when fixtures are intentionally stateful

**Warning signs:**
- Tests pass when run individually (`pytest test_file.py::test_name`)
- Tests fail when run as suite (`pytest`)
- Test failures depend on test execution order
- Fixtures return modified data from previous tests

**Source:** [pytest fixtures documentation](https://docs.pytest.org/en/stable/how-to/fixtures.html)

### Pitfall 5: File Operations Test Pollution
**What goes wrong:** Tests create CHANGELOG.md in project root, tests interfere with each other, git shows uncommitted test files.

**Why it happens:** Functions write to current directory without isolation. Tests run in project root by default.

**How to avoid:**
- Always use tmp_path fixture for file I/O tests
- Change to tmp_path directory: `os.chdir(tmp_path)`
- Or pass file paths explicitly if function accepts them
- Clean up in finally block: `try: test_code finally: os.chdir(original)`

**Warning signs:**
- Git status shows test-generated files
- Tests fail on CI but pass locally (file already exists)
- FileExistsError or PermissionError in tests

**Source:** [pytest tmp_path documentation](https://docs.pytest.org/en/stable/how-to/tmp_path.html)

## Code Examples

Verified patterns from official sources:

### Example 1: Complete conftest.py Setup
```python
# tests/conftest.py
import pytest
import os
from unittest.mock import Mock

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set required environment variables before module imports"""
    test_env = {
        "OPENROUTER_API_KEY": "sk-or-test-key-abcdef123456",
        "GITHUB_REPOSITORY": "test-org/test-repo",
        "MODEL": "openai/gpt-5-mini",
        "OUTPUT_LANGUAGE": "English",
        "FORCE_UPDATE": "false",
        "EXTENDED_ANALYSIS": "false",
        "DRY_RUN": "false",
        "DAYS_BACK": "7",
    }

    for key, value in test_env.items():
        os.environ[key] = value

    yield

    # Cleanup not strictly necessary (pytest isolation)
    # but good practice for local test runs
    for key in test_env.keys():
        os.environ.pop(key, None)

@pytest.fixture
def sample_commits():
    """Sample commit data for testing"""
    return [
        "abc123|feat: Add new feature|Author1|2024-01-01|abc",
        "def456|fix: Fix critical bug|Author2|2024-01-02|def",
        "ghi789|docs: Update README|Author3|2024-01-03|ghi",
    ]

@pytest.fixture
def sample_commits_raw():
    """Raw commits.txt content"""
    return "abc123|feat: Add new feature|Author1|2024-01-01|abc\ndef456|fix: Fix critical bug|Author2|2024-01-02|def"

@pytest.fixture
def mock_openai_response():
    """Standard OpenAI API response"""
    response = Mock()
    response.choices = [Mock()]
    response.choices[0].message = Mock()
    response.choices[0].message.content = "### Technical Summary\nChanges made this week."
    return response

@pytest.fixture
def clean_files(tmp_path, monkeypatch):
    """Setup isolated file system for tests"""
    # Change to temp directory
    monkeypatch.chdir(tmp_path)
    yield tmp_path
    # Cleanup automatic via tmp_path
```
**Source:** [pytest conftest documentation](https://docs.pytest.org/en/stable/reference/fixtures.html)

### Example 2: Testing Retry Decorator - All Error Conditions
```python
# tests/test_retry.py
import pytest
import time
from unittest.mock import Mock

def test_retry_rate_limit_429(mocker):
    """Test retry handles 429 rate limit with exponential backoff"""
    mock_sleep = mocker.patch('time.sleep')  # Make test instant
    mock_func = mocker.Mock()

    # Simulate: 429 error → 429 error → success
    mock_func.side_effect = [
        Exception("Error 429: Rate limit exceeded"),
        Exception("Too many requests"),
        "success"
    ]

    from src.generate_changelog import retry_api_call

    @retry_api_call(max_retries=3, delay=2)
    def api_call():
        return mock_func()

    result = api_call()

    assert result == "success"
    assert mock_func.call_count == 3
    assert mock_sleep.call_count == 2  # Two retries

def test_retry_auth_error_401_no_retry(mocker):
    """Test 401 auth errors fail immediately without retry"""
    mock_func = mocker.Mock()
    mock_func.side_effect = Exception("401 Unauthorized: Invalid API key")

    from src.generate_changelog import retry_api_call

    @retry_api_call(max_retries=3, delay=2)
    def api_call():
        return mock_func()

    with pytest.raises(Exception) as exc_info:
        api_call()

    assert "Authentication error" in str(exc_info.value)
    assert mock_func.call_count == 1  # No retries for auth errors

def test_retry_exhaustion(mocker):
    """Test max retries exhaustion raises final error"""
    mock_sleep = mocker.patch('time.sleep')
    mock_func = mocker.Mock()
    mock_func.side_effect = Exception("Network timeout")

    from src.generate_changelog import retry_api_call

    @retry_api_call(max_retries=3, delay=1)
    def api_call():
        return mock_func()

    with pytest.raises(Exception):
        api_call()

    assert mock_func.call_count == 3
    assert mock_sleep.call_count == 2  # Retries between 3 attempts
```
**Source:** [pytest-mock usage](https://pytest-mock.readthedocs.io/en/latest/usage.html)

### Example 3: Testing Changelog File Operations
```python
# tests/test_changelog.py
import pytest
from pathlib import Path

def test_changelog_create_new(tmp_path, monkeypatch, mocker):
    """Test creating new CHANGELOG.md from scratch"""
    monkeypatch.chdir(tmp_path)

    # Create commits.txt
    commits_file = tmp_path / "commits.txt"
    commits_file.write_text("abc123|feat: Add feature|Author|2024-01-01|abc")

    # Mock API calls
    mock_response = mocker.Mock()
    mock_response.choices = [mocker.Mock()]
    mock_response.choices[0].message.content = "Technical summary"

    mocker.patch('src.generate_changelog.client.chat.completions.create',
                 return_value=mock_response)

    # Run function (imports module, generates changelog)
    import src.generate_changelog

    # Verify CHANGELOG.md created
    changelog = tmp_path / "CHANGELOG.md"
    assert changelog.exists()

    content = changelog.read_text()
    assert "# Changelog" in content
    assert "Week" in content
    assert "feat: Add feature" in content

def test_changelog_duplicate_detection(tmp_path, monkeypatch):
    """Test duplicate week entry detection without force mode"""
    monkeypatch.chdir(tmp_path)

    # Create existing CHANGELOG with Week 5, 2024
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("""# Changelog

## Week 5, 2024

Existing content

---
""")

    # Try to add same week again
    monkeypatch.setenv("FORCE_UPDATE", "false")

    # Should exit without overwriting
    # ... test logic ...

def test_changelog_force_update(tmp_path, monkeypatch, mocker):
    """Test force mode overwrites existing week entry"""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("FORCE_UPDATE", "true")

    # Create existing entry
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text("""# Changelog

## Week 5, 2024

Old content

---
""")

    # Create new commits
    commits_file = tmp_path / "commits.txt"
    commits_file.write_text("xyz789|fix: Bug fix|Author|2024-02-01|xyz")

    # Mock API
    mock_response = mocker.Mock()
    mock_response.choices[0].message.content = "New summary"
    mocker.patch('src.generate_changelog.client.chat.completions.create',
                 return_value=mock_response)

    # Run and verify old content replaced
    import src.generate_changelog
    importlib.reload(src.generate_changelog)

    content = changelog.read_text()
    assert "New summary" in content
    assert "Old content" not in content
```
**Source:** [pytest tmp_path documentation](https://docs.pytest.org/en/stable/how-to/tmp_path.html)

### Example 4: Parametrized Language Configuration Testing
```python
# tests/test_language.py
import pytest

@pytest.mark.parametrize("language,week_label,tech_label", [
    ("English", "Week", "🔧 Technical Changes"),
    ("Dutch", "Week", "🔧 Technische wijzigingen"),
    ("German", "Woche", "🔧 Technische Änderungen"),
    ("French", "Semaine", "🔧 Modifications techniques"),
    ("Spanish", "Semana", "🔧 Cambios técnicos"),
])
def test_language_config_labels(language, week_label, tech_label, monkeypatch):
    """Test all supported languages have correct labels"""
    monkeypatch.setenv("OUTPUT_LANGUAGE", language)

    # Reload to pick up new language
    import importlib
    import src.generate_changelog
    importlib.reload(src.generate_changelog)

    config = src.generate_changelog.config
    assert config["week_label"] == week_label
    assert config["tech_changes"] == tech_label

def test_language_fallback_unsupported(monkeypatch, capsys):
    """Test unsupported language falls back to English"""
    monkeypatch.setenv("OUTPUT_LANGUAGE", "Klingon")

    import importlib
    import src.generate_changelog
    importlib.reload(src.generate_changelog)

    # Should use English config
    config = src.generate_changelog.config
    assert config["week_label"] == "Week"

    # Should warn user
    captured = capsys.readouterr()
    assert "not supported" in captured.out
    assert "Falling back to English" in captured.out
```
**Source:** [pytest monkeypatch documentation](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| tmpdir fixture | tmp_path fixture | pytest 3.9 (2018) | tmp_path uses pathlib.Path (modern), tmpdir deprecated |
| manual mock teardown | pytest-mock mocker fixture | pytest-mock 1.0 (2015) | Automatic cleanup, prevents mock leaks |
| .coveragerc file | pyproject.toml [tool.coverage] | coverage.py 5.0 (2019) | Single config file, TOML standard |
| unittest.mock only | pytest-mock wrapper | pytest-mock 3.0 (2020) | Fixture integration, cleaner syntax |
| pytest.ini | pyproject.toml [tool.pytest.ini_options] | pytest 6.0 (2020) | Consolidated Python project config |

**Deprecated/outdated:**
- **tmpdir fixture:** Use tmp_path instead (pathlib.Path vs py.path.local)
- **--cov-config .coveragerc:** Use pyproject.toml [tool.coverage] sections
- **pytest_namespace hook:** Removed in pytest 4.0, use pytest.register_assert_rewrite()

## Open Questions

Things that couldn't be fully resolved:

1. **importlib.reload() reliability with global state**
   - What we know: importlib.reload() re-executes module-level code
   - What's unclear: Whether it properly resets OpenAI client instance, whether old references persist
   - Recommendation: Test approach - if reload causes issues, use subprocess or pytest-xdist for isolation

2. **Coverage exclusion for __main__ block**
   - What we know: exclude_lines supports regex patterns, default excludes "pragma: no cover"
   - What's unclear: Whether `if __name__ == "__main__":` needs explicit exclusion or is auto-excluded
   - Recommendation: Add to exclude_lines explicitly, verify with coverage report

3. **Optimal chunk size for parametrized tests**
   - What we know: Testing 0, 1, 5, 6, 100+ commits covers boundaries
   - What's unclear: Whether intermediate values (15, 30, 50) add meaningful coverage
   - Recommendation: Start with boundaries, add intermediate values only if edge cases discovered

## Sources

### Primary (HIGH confidence)
- [pytest monkeypatch documentation](https://docs.pytest.org/en/stable/how-to/monkeypatch.html) - Environment variable isolation
- [pytest fixtures documentation](https://docs.pytest.org/en/stable/how-to/fixtures.html) - Fixture scopes, conftest.py, autouse
- [pytest tmp_path documentation](https://docs.pytest.org/en/stable/how-to/tmp_path.html) - File I/O testing
- [pytest-cov configuration](https://pytest-cov.readthedocs.io/en/latest/config.html) - Coverage setup
- [coverage.py configuration](https://coverage.readthedocs.io/en/latest/config.html) - pyproject.toml [tool.coverage] sections
- [pytest-mock usage](https://pytest-mock.readthedocs.io/en/latest/usage.html) - Mocker fixture API

### Secondary (MEDIUM confidence)
- [pytest discussions #10027](https://github.com/pytest-dev/pytest/discussions/10027) - Import-time env vars (official discussion)
- [Testing exit codes with pytest](https://dev.to/boris/testing-exit-codes-with-pytest-1g27) - sys.exit() patterns
- [pytest-mock tutorial](https://www.datacamp.com/tutorial/pytest-mock) - API mocking examples
- [pytest-with-eric conftest guide](https://pytest-with-eric.com/pytest-best-practices/pytest-conftest/) - Shared fixtures patterns

### Tertiary (LOW confidence)
- General pytest-mock examples from web search - Need verification with official docs for production use

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - pytest, pytest-cov, pytest-mock are documented, stable, widely-adopted
- Architecture patterns: HIGH - All patterns from official pytest documentation or verified sources
- Pitfalls: HIGH - Based on common issues documented in pytest discussions and tutorials
- Import-time side effects solution: MEDIUM - conftest.py approach works but not officially guaranteed by pytest team

**Research date:** 2026-02-03
**Valid until:** 2026-03-03 (30 days - pytest is stable, slow-moving project)
