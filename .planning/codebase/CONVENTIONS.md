# Coding Conventions

**Analysis Date:** 2026-02-03

## Naming Patterns

**Files:**
- Python source files use snake_case: `generate_changelog.py`
- Shell scripts and YAML files use appropriate conventions for their language
- Configuration files are descriptive: `action.yml`, `requirements.txt`

**Functions:**
- Snake_case for all function names (Python convention)
- Descriptive names indicating purpose and return type: `process_commits_in_chunks()`, `generate_summary()`, `merge_chunk_summaries()`
- Internal helper functions prefixed with clear intent: `cleanup_temp_files()`, `retry_api_call()` (as decorator)

**Variables:**
- Snake_case for all variable names, matching Python PEP 8
- Environment variables use UPPERCASE_WITH_UNDERSCORES: `OPENROUTER_API_KEY`, `OUTPUT_LANGUAGE`, `FORCE_UPDATE`, `EXTENDED_ANALYSIS`
- Dictionary keys use camelCase or appropriate language convention: `api_key`, `output_language`, `force_update`
- Language configuration dictionaries use snake_case keys: `week_label`, `tech_changes`, `fallback_tech`, `lines_added`

**Types:**
- Python is dynamically typed; type hints not explicitly used in current codebase
- Dictionary structures are well-defined in language configs (e.g., `language_configs` dict structure)

## Code Style

**Formatting:**
- No automated formatter detected (no .prettierrc, autopep8, or black config)
- Manual formatting observed:
  - 4-space indentation (Python standard)
  - Blank lines between logical sections
  - Line length varies; longest observed ~120 characters
  - Consistent use of textwrap.dedent for multi-line strings

**Linting:**
- No linter config detected (.eslintrc, .flake8, pylint.rc, etc.)
- Code follows Python conventions manually:
  - Imports at top of file
  - Whitespace around operators
  - Logical grouping of related code

**Shell Scripts (in action.yml):**
- Bash scripts use consistent spacing and structure
- Heredoc pattern for multi-line strings
- Proper quoting for variables: `"${{ ... }}"`
- Comment headers explaining sections with emoji indicators (🔍, ✅, ⚠️)

## Import Organization

**Order (Python):**
1. Standard library imports (os, sys, datetime, textwrap, time, re)
2. Third-party imports (functools for wraps decorator)
3. External SDK imports (openai)
4. No local imports (single-file application)

**Example from `src/generate_changelog.py` (lines 1-8):**
```python
import os
import sys
import datetime
import textwrap
import time
import re
from functools import wraps
from openai import OpenAI
```

**Path Aliases:**
- No aliases used; direct imports
- Relative file operations use current directory: `open("commits.txt")`, `open("CHANGELOG.md")`

## Error Handling

**Patterns:**
- Decorator-based retry logic with exponential backoff: `@retry_api_call()` decorator (lines 10-79)
- Try/except blocks for file operations and API calls
- Graceful fallback mechanism: if summary generation fails, use pre-defined fallback strings
- Specific error classification:
  - Rate limiting (429): longer backoff with jitter
  - Authentication (401): immediate failure with helpful message
  - Model not found (404): immediate failure with alternatives
  - Network issues: exponential backoff with shorter jitter
  - Generic errors: exponential backoff with standard jitter

**Error Messages:**
- User-friendly with emoji prefixes (❌, 💡, ⏰, 🔌, ⚠️)
- Actionable guidance provided (lines 84-96): where to find API keys, how to validate format
- Errors include suggestions for resolution (lines 37-48)

**Exit Behavior:**
- `sys.exit(1)` for critical failures (missing API key, input validation)
- `sys.exit(0)` for early exits on non-errors (no commits, duplicate entry without force)
- No exit on partial failures; graceful degradation (line 568-571: chunk failure continues)

## Logging

**Framework:** Console printing (no logger library)

**Patterns:**
- Print statements with emoji indicators for status:
  - ✅: Success
  - ❌: Error/Failure
  - 🔄: Processing/Action
  - 📊: Information/Stats
  - 💡: Suggestion/Guidance
  - ⏰: Waiting/Delay
  - 🔌: Network
  - ⚠️: Warning
  - 🧹: Cleanup
  - 🤖: Model info
  - 🌍: Language info

**When to Log:**
- Every major operation start/completion
- Progress indicators for long operations (lines 295-296: chunk processing)
- Error context and suggestions
- Configuration and environment setup
- Cache hits and misses

**Examples from code:**
```python
print(f"🤖 Using model: {model}")
print(f"✅ Found $COMMIT_COUNT commits")
print(f"⚠️  Warning: Only found {total_commits} commits for {days_back} days")
```

## Comments

**When to Comment:**
- Explaining non-obvious logic (rate limiting strategy in retry decorator)
- Section headers explaining multi-step processes (lines 213, 265, 403)
- Warning about edge cases or gotchas

**Examples from code:**
```python
# Handle rate limiting specifically
if "429" in error_str or "rate limit" in error_str...

# Merge all chunk summaries
if len(chunk_summaries) == 1:
```

**JSDoc/TSDoc:**
- Docstrings used for function definitions
- Format: Triple-quoted strings describing purpose
- Example (lines 10-11): `"""Decorator to retry API calls with exponential backoff, jitter, and rate limiting handling"""`

## Function Design

**Size:**
- Most functions 20-60 lines
- Longer functions handle complex logic (generate_chunked_summary: 35 lines, process_commits_in_chunks: ~30 lines)
- Main script execution is inline (not wrapped in main() function), totaling ~720 lines

**Parameters:**
- Functions accept required parameters explicitly
- Decorators use keyword arguments with defaults: `@retry_api_call(max_retries=3, delay=2, timeout=30)`
- Template strings use `.format()` for parameter injection

**Return Values:**
- Functions return data or structured content (summaries as strings)
- Decorator wrapper returns None on final failure after retries
- Generators not used; arrays/lists returned for multi-value returns

**Async/Concurrency:**
- No async/await patterns used
- Sequential execution with specific exceptions:
  - Bash script uses background processes for parallel git operations (action.yml lines 117-133)
  - Python script processes sequentially

## Module Design

**Exports:**
- Single-file application; no explicit exports
- Script runs as entry point via GitHub Actions

**Barrel Files:**
- Not applicable (single Python file, no module structure)

**Organization:**
- Configuration dictionaries at top (language_configs, date_formats)
- Utility functions defined before use (retry decorator, cleanup, process functions)
- Main execution flow at module level (API key validation, client setup, file operations)
- Error handling wraps main operations (try/except at lines 217, 617)

## Special Patterns

**Language Configuration Pattern:**
Dictionary structure used for multi-language support (lines 118-209):
```python
language_configs = {
    "English": { ... },
    "Dutch": { ... },
    ...
}
config = language_configs.get(output_language, language_configs["English"])
```

**Template Prompt Pattern:**
Using `textwrap.dedent()` with `.format()` for prompt injection (lines 404-454, 457-500):
```python
tech_prompt_template = textwrap.dedent(f"""...""").strip()
# Later:
prompt = prompt_template.format(base_context=base_context)
```

**Decorator Pattern:**
Retry logic implemented as reusable decorator (lines 10-79):
```python
@retry_api_call(max_retries=3, delay=2, timeout=30)
def merge_chunk_summaries(...):
```

**Graceful Degradation Pattern:**
Operations continue with fallbacks on partial failures (lines 568-571):
```python
try:
    chunk_summary = generate_summary(...)
except Exception as e:
    print(f"⚠️  Warning: Failed to generate ...")
    chunk_summaries.append(f"[Chunk {chunk_idx + 1} analysis failed ...]")
    # Continue processing other chunks
```

---

*Convention analysis: 2026-02-03*
