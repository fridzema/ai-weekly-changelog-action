# Domain Pitfalls: Retrofitting Tests to Existing Python Code

**Domain:** Adding test coverage to a 723-line Python script with external dependencies
**Researched:** 2026-02-03
**Confidence:** HIGH (verified with official pytest docs, current best practices)

## Executive Summary

Adding tests to existing code that was written without testability in mind creates unique challenges distinct from greenfield TDD. The primary risks are: over-mocking leading to brittle test suites, tight coupling making code untestable, and creating maintenance burdens that discourage regular test execution.

For this specific codebase (API calls, file I/O, retry logic, environment variables), the biggest pitfall is **testing implementation rather than behavior**, which leads to tests that break when refactoring even if functionality is preserved.

## Critical Pitfalls

Mistakes that cause rewrites, major refactors, or abandoned test suites.

### Pitfall 1: Patching Built-in Functions Directly

**What goes wrong:**
Mocking built-in functions like `open()`, `time.sleep()`, or `random.uniform()` directly can break pytest's internals and create fragile tests that fail in unexpected ways.

**Why it happens:**
The existing code uses built-ins throughout (file I/O, time.sleep in retry logic, random.uniform for jitter). The instinct is to mock these where they're defined rather than where they're used.

**Consequences:**
- Tests fail with cryptic errors unrelated to code changes
- pytest's internal mechanisms break (e.g., pytest's own file handling)
- Test isolation fails when mocks leak between tests
- Cannot run tests in parallel due to global state pollution

**Prevention:**
1. **Extract dependencies into injectable components**
   ```python
   # BAD: Hard to test
   def retry_with_backoff():
       time.sleep(delay * (2 ** attempt))

   # GOOD: Injectable sleep function
   def retry_with_backoff(sleep_func=time.sleep):
       sleep_func(delay * (2 ** attempt))
   ```

2. **Use MonkeyPatch.context() for stdlib mocking**
   ```python
   # When you MUST mock builtins, limit scope
   def test_file_reading(monkeypatch):
       with monkeypatch.context() as m:
           m.setattr('builtins.open', mock_open(read_data="test"))
           # Test code here - mock only affects this block
   ```

3. **Create seams via wrapper functions**
   ```python
   # Wrap built-ins to create testable seams
   class FileSystem:
       def read_file(self, path):
           with open(path, 'r') as f:
               return f.read()

   # Now you can mock FileSystem instead of open()
   ```

**Detection:**
- Tests fail when run with `--tb=native --assert=plain --capture=no`
- Parallel test execution (`-n auto` with pytest-xdist) fails
- Error messages mention "fixture" or "internal" when testing file operations
- Tests pass individually but fail when run together

**Official Source:** [pytest monkeypatch documentation](https://docs.pytest.org/en/stable/how-to/monkeypatch.html) explicitly warns: "It is not recommended to patch builtin functions such as open, compile, etc., because it might break pytest's internals."

---

### Pitfall 2: Testing Mock Configuration Instead of Real Behavior

**What goes wrong:**
Tests verify that mocks were called correctly rather than verifying the actual business logic. This creates false confidence - tests pass but real bugs slip through.

**Why it happens:**
When retrofitting tests to tightly coupled code, mocking becomes easier than refactoring. You end up with tests like:
```python
def test_generate_summary(mock_openai):
    mock_openai.chat.completions.create.return_value = Mock()
    generate_summary("prompt", "description")
    mock_openai.chat.completions.create.assert_called_once()  # Verifies mock, not logic
```

**Consequences:**
- Tests pass but real functionality is broken
- Refactoring breaks tests even when behavior is preserved
- Tests become coupled to implementation details
- Cannot detect integration issues (mocks don't match reality)

**Prevention:**
1. **Test behavior, not implementation**
   ```python
   # BAD: Tests that mock was called
   @patch('generate_changelog.client')
   def test_summary_generation(mock_client):
       mock_client.chat.completions.create.return_value = mock_response
       result = generate_summary(prompt, "tech")
       mock_client.chat.completions.create.assert_called_once()  # Brittle!

   # GOOD: Tests actual behavior
   @patch('generate_changelog.client')
   def test_summary_generation_returns_formatted_markdown(mock_client):
       mock_client.chat.completions.create.return_value = mock_response_with_content("# Summary")
       result = generate_summary(prompt, "tech")
       assert "###" in result  # Verifies markdown formatting
       assert len(result) > 50  # Verifies non-empty
   ```

2. **Use real objects with fake backends where possible**
   ```python
   # Instead of mocking OpenAI client, use a fake implementation
   class FakeOpenAIClient:
       def __init__(self, responses):
           self.responses = responses
           self.call_count = 0

       def chat_completions_create(self, **kwargs):
           response = self.responses[self.call_count]
           self.call_count += 1
           return response
   ```

3. **Limit assertion scope to public interface**
   - Assert on return values, not call counts
   - Assert on side effects (files written, state changed), not mock interactions
   - Use `assert_called_with()` only when call parameters ARE the behavior

**Detection:**
- Your tests have more lines of mock setup than assertions
- Tests fail when you rename private methods
- Refactoring working code breaks tests
- `assert_called_once()` appears without corresponding behavior assertions

---

### Pitfall 3: Not Resetting Mocks and Environment State Between Tests

**What goes wrong:**
Tests pass individually but fail when run in certain orders. Mock state or environment variables leak between tests, creating non-deterministic failures.

**Why it happens:**
The codebase reads environment variables at module import time (lines 82-109) and creates a global `client` object. Tests don't clean up properly.

**Consequences:**
- Tests pass in isolation (`pytest test_foo.py::test_one`) but fail in full suite
- Different test execution orders produce different results
- CI failures that cannot be reproduced locally
- Developers waste hours debugging "flaky tests"

**Prevention:**
1. **Use pytest fixtures with proper cleanup**
   ```python
   @pytest.fixture
   def mock_env():
       """Fixture that automatically cleans up environment changes"""
       original_env = os.environ.copy()
       yield
       os.environ.clear()
       os.environ.update(original_env)

   @pytest.fixture(autouse=True)
   def reset_client():
       """Automatically reset client between tests"""
       yield
       # Cleanup happens after test
       importlib.reload(generate_changelog)  # Reset module state
   ```

2. **Use monkeypatch fixture for env vars (auto-cleanup)**
   ```python
   def test_with_env_var(monkeypatch):
       monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
       monkeypatch.setenv("MODEL", "test-model")
       # Automatically restored after test
   ```

3. **Avoid module-level side effects**
   ```python
   # BAD: Executed at import time
   client = OpenAI(api_key=os.getenv("OPENROUTER_API_KEY"))

   # GOOD: Lazy initialization
   _client = None
   def get_client():
       global _client
       if _client is None:
           _client = OpenAI(api_key=os.getenv("OPENROUTER_API_KEY"))
       return _client
   ```

**Detection:**
- Run tests in random order: `pytest --random-order`
- Test results change when adding/removing other tests
- Tests pass when run alone: `pytest -k test_specific` but fail in suite
- Environment variables from one test affect another

**Official Source:** [pytest-with-eric: Unit Testing Best Practices](https://pytest-with-eric.com/introduction/python-unit-testing-best-practices/) - "Tests that depend on each other create maintenance nightmares. Each test must be able to run alone, and also within the test suite, regardless of the order that they are called."

---

### Pitfall 4: Over-Mocking Creates Maintenance Burden

**What goes wrong:**
Every test has 20+ lines of mock setup. Small code changes require updating dozens of tests. Team stops adding tests because it's too painful.

**Why it happens:**
When code has tight coupling and deep dependency chains, mocking becomes recursive - you mock the API client, then mock its methods, then mock the response object, then mock the message attribute...

**Consequences:**
- Test code is 3-5x larger than production code
- Refactoring becomes prohibitively expensive
- Tests take longer to write than features
- Team abandons testing as unmaintainable

**Prevention:**
1. **Create test helpers and builders**
   ```python
   # Helper to reduce mock boilerplate
   def mock_openai_response(content, model="test-model"):
       response = Mock()
       response.choices = [Mock()]
       response.choices[0].message.content = content
       return response

   def test_summary_generation():
       with patch('generate_changelog.client.chat.completions.create',
                  return_value=mock_openai_response("# Summary")):
           result = generate_summary(prompt, "tech")
           assert "Summary" in result
   ```

2. **Identify and extract the "seam" for dependency injection**
   ```python
   # Instead of mocking deep into OpenAI client internals,
   # extract the API call into a function you can inject

   def make_api_call(client, model, messages, max_tokens):
       """Seam for testing - single point to mock"""
       return client.chat.completions.create(
           model=model, messages=messages, max_tokens=max_tokens
       )

   def generate_summary(prompt, description, api_call_func=make_api_call):
       response = api_call_func(client, model, messages, max_tokens)
       return response.choices[0].message.content
   ```

3. **Use fixture factories for common mock patterns**
   ```python
   @pytest.fixture
   def api_client_factory():
       def _create_client(responses):
           mock = Mock()
           mock.chat.completions.create.side_effect = [
               mock_openai_response(r) for r in responses
           ]
           return mock
       return _create_client

   def test_retry_logic(api_client_factory):
       client = api_client_factory(["Success"])  # Simple, readable
   ```

**Detection:**
- More than 10 lines of mock setup per test
- Changes to function signatures require updating 10+ tests
- Mock setup code is duplicated across multiple test files
- Developers actively avoid writing tests

---

### Pitfall 5: Testing Retry Logic With Real Sleeps

**What goes wrong:**
Tests for exponential backoff retry logic call `time.sleep()` with real delays, making test suite slow (2+ minutes for retry tests alone).

**Why it happens:**
The `@retry_api_call` decorator uses `time.sleep()` with exponential backoff. Without mocking time, testing retry logic means actually waiting.

**Consequences:**
- Test suite takes minutes instead of seconds
- Developers skip running tests locally
- CI/CD pipelines become bottlenecks
- Tests become non-deterministic (timing-dependent failures)

**Prevention:**
1. **Mock time.sleep for retry tests**
   ```python
   @patch('generate_changelog.time.sleep')
   def test_retry_with_exponential_backoff(mock_sleep):
       with patch('generate_changelog.client.chat.completions.create',
                  side_effect=[Exception("Rate limit"), Mock()]):
           result = generate_summary(prompt, "tech")

           # Verify backoff without waiting
           assert mock_sleep.call_count == 1
           sleep_time = mock_sleep.call_args[0][0]
           assert 2 <= sleep_time <= 10  # Within expected range
   ```

2. **Use pytest-timeout to catch accidental real sleeps**
   ```python
   @pytest.mark.timeout(1)  # Fail if test takes >1 second
   def test_retry_logic():
       # If this sleeps for real, timeout will catch it
       pass
   ```

3. **Extract sleep logic for testing**
   ```python
   def calculate_backoff(attempt, base_delay, jitter_func=random.uniform):
       return base_delay * (2 ** attempt) + jitter_func(0.1, 1)

   def test_backoff_calculation():
       # Test calculation without sleeping
       backoff = calculate_backoff(0, 2, jitter_func=lambda a,b: 0.5)
       assert backoff == 2.5

       backoff = calculate_backoff(2, 2, jitter_func=lambda a,b: 0.5)
       assert backoff == 8.5
   ```

**Detection:**
- Test suite takes >5 seconds for a small number of tests
- CI logs show tests waiting/sleeping
- Test execution time increases linearly with retry test count
- Run with verbose timing: `pytest --durations=10`

**Official Source:** [Python Retry Logic with Tenacity](https://python.useinstructor.com/concepts/retrying/) recommends setting "fewer retries to avoid overwhelming servers" and mocking for tests. [Mozilla bug 687976](https://bugzilla.mozilla.org/show_bug.cgi?id=687976) demonstrates unit testing retry functions without real delays.

---

## Moderate Pitfalls

Mistakes that cause delays, technical debt, or harder maintenance.

### Pitfall 6: Testing File I/O With Real File System

**What goes wrong:**
Tests create real files on disk, leading to conflicts when tests run in parallel and cleanup failures leaving test artifacts.

**Why it happens:**
The script reads `commits.txt`, `commits_extended.txt`, `files_changed.txt` and writes `CHANGELOG.md`. Easy path is testing with real files.

**Consequences:**
- Parallel tests fail (both try to read/write same files)
- Test artifacts pollute repository
- Cleanup failures cause subsequent test failures
- Tests are slower (disk I/O overhead)

**Prevention:**
1. **Use pytest tmp_path fixture**
   ```python
   def test_changelog_writing(tmp_path):
       commits_file = tmp_path / "commits.txt"
       commits_file.write_text("hash|subject|author|date|short")

       changelog_file = tmp_path / "CHANGELOG.md"
       # Test with isolated files in tmp_path
       # Automatically cleaned up after test
   ```

2. **Use monkeypatch to redirect file paths**
   ```python
   def test_reads_commits(monkeypatch, tmp_path):
       commits_file = tmp_path / "commits.txt"
       commits_file.write_text("test data")

       monkeypatch.chdir(tmp_path)  # Change to tmp directory
       # Now code reads from tmp_path
   ```

3. **Extract file operations into testable interface**
   ```python
   class FileReader:
       def read_commits(self, path="commits.txt"):
           with open(path, 'r') as f:
               return f.read()

   # Test with FakeFileReader instead of mocking open()
   ```

**Detection:**
- Test directory contains `.txt` or `.md` files after test run
- Tests fail when run with `pytest -n auto` (parallel)
- Test failures mention "file already exists" or "permission denied"

---

### Pitfall 7: Not Testing Error Conditions

**What goes wrong:**
Tests only cover happy path. Error handling code (which is most of the retry decorator) is never tested.

**Why it happens:**
Happy path is easier to test. Error scenarios require complex mock setups to simulate failures.

**Consequences:**
- Error handling has bugs (never executed in tests)
- Retry logic fails in production (never tested)
- User-facing error messages are wrong (never verified)

**Prevention:**
1. **Use parameterized tests for error scenarios**
   ```python
   @pytest.mark.parametrize("error,expected_message", [
       ("401", "Authentication failed"),
       ("429", "Rate limit exceeded"),
       ("404", "Model error"),
       ("timeout", "Network connectivity issues"),
   ])
   def test_error_handling(error, expected_message, capsys):
       with patch('generate_changelog.client.chat.completions.create',
                  side_effect=Exception(error)):
           with pytest.raises(Exception):
               generate_summary(prompt, "tech")

       captured = capsys.readouterr()
       assert expected_message in captured.out
   ```

2. **Test retry behavior explicitly**
   ```python
   def test_retries_three_times_then_fails():
       call_count = 0
       def failing_api_call(*args, **kwargs):
           nonlocal call_count
           call_count += 1
           raise Exception("Network error")

       with patch('generate_changelog.client.chat.completions.create',
                  side_effect=failing_api_call):
           with pytest.raises(Exception):
               generate_summary(prompt, "tech")

       assert call_count == 3  # Verify retry count
   ```

3. **Test fallback mechanisms**
   ```python
   def test_uses_fallback_on_api_failure():
       with patch('generate_changelog.client.chat.completions.create',
                  side_effect=Exception("API down")):
           # Should not raise, should use fallback
           # (Current code at line 586-587)
           result = generate_chunked_summary([], template, "tech summary", "technical")
           assert result == config['fallback_tech']
   ```

**Detection:**
- Code coverage shows retry decorator has 0% coverage
- Exception handling blocks are marked "not covered"
- Run coverage: `pytest --cov=generate_changelog --cov-report=html`

---

### Pitfall 8: Fixtures With Hidden Side Effects

**What goes wrong:**
Fixtures that modify global state or have hidden dependencies cause tests to interfere with each other.

**Why it happens:**
Using `autouse=True` fixtures or fixtures that modify module-level variables without proper cleanup.

**Consequences:**
- Test order matters (violates independence)
- Debugging is difficult (hidden setup in fixtures)
- Tests fail sporadically

**Prevention:**
1. **Avoid autouse fixtures unless necessary**
   ```python
   # BAD: Every test gets this whether needed or not
   @pytest.fixture(autouse=True)
   def setup_everything():
       setup_database()
       setup_api_client()
       setup_config()

   # GOOD: Explicit dependencies
   @pytest.fixture
   def api_client():
       return setup_api_client()

   def test_something(api_client):  # Explicitly requests what it needs
       pass
   ```

2. **Use yield for teardown**
   ```python
   @pytest.fixture
   def api_client():
       client = setup_client()
       yield client
       # Cleanup always runs
       client.close()
   ```

3. **Make fixture scope explicit**
   ```python
   @pytest.fixture(scope="function")  # New instance per test (default)
   def isolated_client():
       return create_client()

   @pytest.fixture(scope="module")  # Shared across tests (use carefully)
   def shared_config():
       return load_config()
   ```

**Detection:**
- Tests pass when run individually but fail in suite
- Test failures disappear when you add/remove unrelated tests
- Difficult to understand what test depends on

**Official Source:** [pytest fixtures documentation](https://docs.pytest.org/en/stable/how-to/fixtures.html) warns about exception handling in fixtures: "If a yield fixture raises an exception before yielding, pytest won't try to run the teardown code after that yield fixture's yield statement."

---

### Pitfall 9: Poor Test Organization

**What goes wrong:**
All tests in single file `test_generate_changelog.py` grows to 2000+ lines. Cannot find tests, cannot reuse fixtures.

**Why it happens:**
Starting with simple test file and not reorganizing as it grows.

**Consequences:**
- Hard to find relevant tests
- Slow test discovery
- Fixture reuse is difficult
- Merge conflicts in test files

**Prevention:**
1. **Organize by feature/module**
   ```
   tests/
     conftest.py          # Shared fixtures
     test_retry_logic.py
     test_api_calls.py
     test_file_io.py
     test_changelog_formatting.py
     test_chunking.py
   ```

2. **Use conftest.py for shared fixtures**
   ```python
   # tests/conftest.py
   @pytest.fixture
   def mock_openai_client():
       # Available to all tests automatically
       pass

   @pytest.fixture
   def sample_commits():
       return ["hash1|subject1|author1|date1|short1"]
   ```

3. **Use markers for test categories**
   ```python
   @pytest.mark.unit
   def test_backoff_calculation():
       pass

   @pytest.mark.integration
   def test_full_changelog_generation():
       pass

   # Run only unit tests: pytest -m unit
   # Skip integration tests: pytest -m "not integration"
   ```

**Detection:**
- Single test file >500 lines
- Searching for test by name is difficult
- Multiple developers have merge conflicts in test files

**Official Source:** [pytest-with-eric: 5 Best Practices For Organizing Tests](https://pytest-with-eric.com/pytest-best-practices/pytest-organize-tests/) recommends "Use pytest markers to categorise and selectively run tests, such as unit (Fast, isolated unit tests), integration (Tests that integrate with external systems), and slow (Tests that are slow to run)."

---

## Minor Pitfalls

Mistakes that cause annoyance but are fixable.

### Pitfall 10: Unclear Test Names

**What goes wrong:**
Test names like `test_1()`, `test_summary()` don't indicate what they're testing.

**Prevention:**
```python
# BAD
def test_summary():
    pass

# GOOD
def test_generate_summary_returns_markdown_with_headers():
    pass

def test_generate_summary_raises_on_empty_response():
    pass
```

---

### Pitfall 11: Missing Assertions

**What goes wrong:**
Tests run code but don't verify anything (no assertions).

**Prevention:**
```python
# BAD
def test_process_commits():
    process_commits_in_chunks(commits_raw)  # No assertion!

# GOOD
def test_process_commits_returns_formatted_list():
    result, links = process_commits_in_chunks(commits_raw)
    assert len(result) > 0
    assert all('•' in item for item in result)
```

---

### Pitfall 12: Hardcoded Test Data

**What goes wrong:**
Tests break when you change test data format.

**Prevention:**
```python
# Use fixtures or builders
@pytest.fixture
def sample_commit_line():
    return "abc123|feat: add feature|John Doe|2026-02-03|abc"

def test_commit_parsing(sample_commit_line):
    result = parse_commit(sample_commit_line)
    assert result['author'] == "John Doe"
```

---

## Phase-Specific Warnings

Roadmap should address these in order:

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|----------------|------------|
| **Phase 1: Basic unit tests** | Pitfall 2 (testing mocks not behavior) | Start with pure functions (calculate_backoff, format_date) that don't need mocks |
| **Phase 2: Testing retry logic** | Pitfall 5 (real sleeps) | Mock time.sleep from start, use pytest-timeout |
| **Phase 3: Testing file I/O** | Pitfall 1 (patching builtins), Pitfall 6 (real filesystem) | Use tmp_path fixture, extract file ops to wrapper class |
| **Phase 4: Testing API calls** | Pitfall 2 (over-mocking), Pitfall 4 (maintenance burden) | Create test helpers early, use fake client instead of deep mocks |
| **Phase 5: Integration tests** | Pitfall 3 (state leakage) | Use module-scoped fixtures with proper cleanup |
| **Phase 6: CI/CD integration** | Pitfall 7 (missing error tests) | Add coverage requirements, fail CI if <80% |

## Codebase-Specific Warnings

### Global Client Initialization
Lines 82-109 create global `client` object at module import. This makes testing difficult:
- **Problem:** Cannot inject test client without modifying module state
- **Solution:** Extract to `get_client()` function with lazy initialization
- **Impact Phase:** Phase 4 (API testing)

### Decorator Testing Complexity
The `@retry_api_call` decorator (lines 10-79) is complex to test:
- **Problem:** Decorators wrap functions, making it hard to test in isolation
- **Solution:** Test decorated functions as black boxes, verify behavior not internals
- **Impact Phase:** Phase 2 (retry logic)

### Module-Level Configuration
Lines 105-211 read environment variables at import time:
- **Problem:** Hard to test with different configurations
- **Solution:** Use monkeypatch.setenv BEFORE importing module, or reload module
- **Impact Phase:** Phase 1 (basic setup)

### Nested Function Calls
`generate_chunked_summary` calls `generate_summary` calls `merge_chunk_summaries`:
- **Problem:** Deep call stack requires mocking at multiple levels
- **Solution:** Test each level independently first, then integration test the whole chain
- **Impact Phase:** Phase 4 (API testing)

## Sources

**HIGH CONFIDENCE (Official Documentation):**
- [pytest monkeypatch documentation](https://docs.pytest.org/en/stable/how-to/monkeypatch.html) - Warning about patching builtins
- [pytest fixtures documentation](https://docs.pytest.org/en/stable/how-to/fixtures.html) - Fixture setup/teardown patterns
- [How to Mock Environment Variables in pytest - Adam Johnson](https://adamj.eu/tech/2020/10/13/how-to-mock-environment-variables-with-pytest/) - Environment variable testing

**MEDIUM CONFIDENCE (Established Best Practices):**
- [Python Unit Testing Best Practices | Pytest with Eric](https://pytest-with-eric.com/introduction/python-unit-testing-best-practices/) - Test independence
- [5 Best Practices For Organizing Tests | Pytest with Eric](https://pytest-with-eric.com/pytest-best-practices/pytest-organize-tests/) - Test organization and markers
- [Pytest Conftest With Best Practices | Pytest with Eric](https://pytest-with-eric.com/pytest-best-practices/pytest-conftest/) - conftest.py patterns
- [Testing APIs with PyTest: Mocks in Python | CodiLime](https://codilime.com/blog/testing-apis-with-pytest-mocks-in-python/) - API mocking patterns
- [How To Mock In Pytest? | Pytest with Eric](https://pytest-with-eric.com/mocking/pytest-mocking/) - Mock best practices
- [Python Retry Logic with Tenacity](https://python.useinstructor.com/concepts/retrying/) - Testing retry logic

**MEDIUM CONFIDENCE (Community Patterns):**
- [Retrofitting Tests To Legacy Code | DevJoy](https://www.devjoy.com/blog/retrofitting-tests-to-legacy-code/) - Legacy code patterns
- [How to Structure Large Test Suites in Python Using pytest](https://woteq.com/how-to-structure-large-test-suites-in-python-using-pytest/) - Large test suite organization
- [Mocking External Services in Pytest | IntelliNotebook](https://intellinotebook.com/programming/test-automation/mocking-external-services-in-pytest/) - External service mocking

**Research Notes:**
- All pytest documentation verified as current (stable version)
- Best practices cross-referenced across multiple sources
- Pitfalls verified against actual codebase structure (723-line generate_changelog.py)
- Focus on retrofitting vs greenfield TDD based on [DevJoy retrofit article](https://www.devjoy.com/blog/retrofitting-tests-to-legacy-code/)
