# Phase 3: Code Quality Tooling - Research

**Researched:** 2026-02-03
**Domain:** Python code quality tooling (linting, formatting, type checking, security scanning)
**Confidence:** HIGH

## Summary

Phase 3 introduces modern Python quality tooling to establish consistent code style, catch bugs early, ensure type safety, and identify security vulnerabilities. The project already has pyproject.toml with pytest configuration, making it the natural location for all quality tool configurations.

The primary recommendation is to use Ruff for both linting and formatting (replacing the need for separate tools like Flake8, Black, and isort), mypy for type checking, and pip-audit for dependency vulnerability scanning. Notably, Ruff includes native implementations of Bandit's security rules (S prefix), eliminating the need for a separate Bandit installation while providing 10-100x faster execution.

**Primary recommendation:** Configure Ruff with security rules (S) to cover QUAL-01 through QUAL-04 in one tool, add mypy for type checking (QUAL-06, QUAL-07), and pip-audit for dependency scanning (QUAL-05).

## Standard Stack

The established tools for Python code quality in 2025/2026:

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| ruff | 0.14.x | Linting + formatting | 10-100x faster than alternatives, replaces Flake8/Black/isort/Bandit in one tool, written in Rust |
| mypy | 1.19+ | Static type checking | De facto standard for Python type checking, mature ecosystem |
| pip-audit | 2.10.0 | Dependency vulnerability scanning | Official PyPA tool, uses Python Packaging Advisory Database |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| types-requests | latest | Type stubs for requests library | When project uses requests (this project does) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| ruff format | black | Black is original formatter, but Ruff is faster and consolidates tools |
| ruff lint | flake8 + plugins | Flake8 is mature but requires multiple plugins; Ruff includes 800+ rules natively |
| ruff S rules | bandit | Bandit is standalone tool; Ruff implements same rules 100x faster |
| mypy | ty (Astral) | ty is new from Ruff creators, but mypy is more mature and stable as of 2026 |
| pip-audit | safety | Safety requires commercial license; pip-audit is fully open source from PyPA |

**Installation:**
```bash
pip install ruff mypy pip-audit types-requests
```

Add to requirements-dev.txt:
```
ruff>=0.14.0
mypy>=1.19
pip-audit>=2.10.0
types-requests
```

## Architecture Patterns

### Recommended pyproject.toml Structure

```toml
# Existing pytest/coverage config stays in place

[tool.ruff]
target-version = "py39"
line-length = 88
exclude = [".venv", "build", "dist", ".git"]

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "S",      # flake8-bandit (security)
    "UP",     # pyupgrade
]
ignore = [
    "E501",   # line too long (handled by formatter)
]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101"]  # Allow assert in tests

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.9"
strict = false
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true

[[tool.mypy.overrides]]
module = "tests.*"
ignore_errors = true
```

### Pattern 1: Incremental Type Hints

**What:** Add type hints to public functions first, then expand gradually
**When to use:** Existing codebase without type hints (this project)
**Example:**
```python
# Before
def get_language_config(language):
    """Get language configuration for changelog generation."""
    ...

# After
def get_language_config(language: str) -> dict[str, str]:
    """Get language configuration for changelog generation."""
    ...
```

### Pattern 2: Ruff Security Rules (S prefix)

**What:** Enable Ruff's built-in Bandit-compatible security checks
**When to use:** Instead of standalone Bandit for faster, integrated security scanning
**Key rules:**
- S101: assert used (allow in tests via per-file-ignores)
- S105-S107: hardcoded passwords
- S301-S302: pickle/marshal usage
- S608: SQL injection

### Pattern 3: Pre-commit Optional (Future CI/CD)

**What:** Run quality tools in pre-commit hooks
**When to use:** Phase 4 (CI/CD Pipeline) - not needed for Phase 3
**Note:** Phase 3 focuses on configuration and fixing issues; Phase 4 adds automation

### Anti-Patterns to Avoid

- **Enabling too many rules at once:** Start with core rules (E, W, F, I, B, S) then expand. Adding all 800+ rules creates overwhelming noise.
- **Using strict mypy on legacy code:** Start with `strict = false` and individual strictness flags, not `strict = true` on untyped codebase.
- **Mixing Bandit with Ruff S rules:** Redundant; Ruff's S rules are the same checks, just faster.
- **Ignoring per-file-ignores for tests:** Tests legitimately use `assert` statements; ignoring S101 in tests is correct.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Import sorting | Manual reordering | Ruff `I` rules + `ruff format` | Automatic, consistent, handles complex cases |
| Code formatting | Style guide enforcement | `ruff format` | Opinionated, zero-config, Black-compatible |
| Security scanning | Manual code review for common issues | Ruff `S` rules | Catches 40+ common security anti-patterns |
| Dependency CVE checking | Checking CVE databases manually | pip-audit | Uses authoritative PyPI Advisory Database |
| Type stub generation | Writing custom .pyi files | types-requests and similar packages | Community-maintained, auto-updated |

**Key insight:** Modern Python tooling has consolidated dramatically. Ruff alone replaces 7+ separate tools (Flake8, Black, isort, pyupgrade, autoflake, pydocstyle, Bandit) while being 10-100x faster.

## Common Pitfalls

### Pitfall 1: Line Length Conflicts Between Linter and Formatter

**What goes wrong:** Ruff lint complains about long lines, then Ruff format doesn't fix them
**Why it happens:** Default E501 (line too long) conflicts with formatter's inability to shorten all lines
**How to avoid:** Ignore E501 in lint config; let formatter handle line breaks where possible
**Warning signs:** Endless cycle of lint errors that formatting doesn't resolve

### Pitfall 2: Mypy Fails on Third-Party Libraries Without Stubs

**What goes wrong:** mypy errors on `import requests` or similar
**Why it happens:** Libraries without inline types or stubs cause "missing type stubs" errors
**How to avoid:** Use `ignore_missing_imports = true` globally, or install type stubs (types-requests)
**Warning signs:** Errors like `Cannot find implementation or library stub for module named "requests"`

### Pitfall 3: Tests Fail After Ruff Formatting Changes

**What goes wrong:** Formatting changes break string comparisons or snapshot tests
**Why it happens:** Ruff may normalize string quotes or whitespace differently than before
**How to avoid:** Run tests immediately after formatting; review test failures for format-induced issues
**Warning signs:** Tests pass before formatting, fail after

### Pitfall 4: S101 Assert Errors in Test Files

**What goes wrong:** Ruff security rules flag all assert statements as security issues
**Why it happens:** S101 warns that assert statements are stripped in optimized Python (-O flag)
**How to avoid:** Add per-file-ignores for test directories: `"tests/*" = ["S101"]`
**Warning signs:** Hundreds of S101 violations in test files

### Pitfall 5: Over-Ambitious Type Hint Migration

**What goes wrong:** Adding `strict = true` to mypy causes 100+ errors on first run
**Why it happens:** Strict mode enables all checks; legacy code has many implicit types
**How to avoid:** Start with `strict = false`, add individual flags incrementally
**Warning signs:** mypy finds more errors than expected; developers ignore all mypy output

## Code Examples

Verified patterns from official sources:

### Minimal Ruff Configuration for This Project

```toml
# Source: https://docs.astral.sh/ruff/configuration/
[tool.ruff]
target-version = "py39"
line-length = 88

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "S", "UP"]
ignore = ["E501"]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### Mypy Configuration for Gradual Adoption

```toml
# Source: https://mypy.readthedocs.io/en/stable/config_file.html
[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
# Don't start with strict = true on legacy code
check_untyped_defs = true

[[tool.mypy.overrides]]
module = "tests.*"
ignore_errors = true
```

### Type Hints for Public Functions

```python
# Source: https://typing.python.org/en/latest/reference/best_practices.html
from typing import Any

def redact_api_key(text: str) -> str:
    """Redact API key from error messages."""
    ...

def get_language_config(language: str) -> dict[str, str]:
    """Get language configuration for changelog generation."""
    ...

def process_commits_in_chunks(
    commits_raw: str,
    repo_url: str | None = None,
    chunk_size: int = 50
) -> tuple[list[str], list[str]]:
    """Process commits in chunks."""
    ...

def retry_api_call(
    max_retries: int = 3,
    delay: int = 2,
    timeout: int = 30
) -> Any:  # Returns decorator
    """Decorator to retry API calls."""
    ...
```

### Running Quality Tools

```bash
# Lint check (no changes)
ruff check src/ tests/

# Lint with auto-fix
ruff check --fix src/ tests/

# Format check (no changes)
ruff format --check src/ tests/

# Format apply
ruff format src/ tests/

# Type check
mypy src/

# Security/dependency audit
pip-audit -r requirements.txt
pip-audit -r requirements-dev.txt
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Flake8 + Black + isort | Ruff (all-in-one) | 2023-2024 | Single tool, 100x faster |
| Bandit standalone | Ruff S rules | 2024 | Integrated, same rules, faster |
| setup.cfg configuration | pyproject.toml | PEP 518/621 (2020-2022) | Single config file for all tools |
| `typing.List[str]` | `list[str]` | Python 3.9 (2020) | Native generics, no import needed |
| `typing.Optional[X]` | `X \| None` | Python 3.10 (2021) | Union syntax simplification |

**Deprecated/outdated:**
- Flake8: Still works, but Ruff is faster and consolidates plugins
- Black: Still works, but Ruff format is drop-in replacement
- bandit standalone: Ruff S rules are faster, integrated
- setup.cfg: pyproject.toml is the modern standard

## Open Questions

Things that couldn't be fully resolved:

1. **Which openai library version needs type stubs?**
   - What we know: openai>=1.14 is used; modern openai has inline types
   - What's unclear: Whether types-openai is needed or if inline types suffice
   - Recommendation: Start without types-openai; add if mypy complains

2. **Exact Ruff version for stability**
   - What we know: 0.14.x is current, pre-1.0 with potential breaking changes
   - What's unclear: How stable rule behavior is across minor versions
   - Recommendation: Pin to specific version (e.g., ruff>=0.14.0,<0.15.0)

## Sources

### Primary (HIGH confidence)
- [Ruff Configuration](https://docs.astral.sh/ruff/configuration/) - Full pyproject.toml structure, rule sets
- [Ruff Linter Rules](https://docs.astral.sh/ruff/linter/) - Rule categories (E, W, F, I, B, S, UP)
- [Mypy Config File](https://mypy.readthedocs.io/en/stable/config_file.html) - pyproject.toml format, options
- [pip-audit on PyPI](https://pypi.org/project/pip-audit/) - Version 2.10.0, usage, options
- [Bandit Configuration](https://bandit.readthedocs.io/en/latest/config.html) - pyproject.toml format (though Ruff S rules preferred)

### Secondary (MEDIUM confidence)
- [Python Developer Tooling Handbook - Ruff Defaults](https://pydevtools.com/handbook/how-to/how-to-configure-recommended-ruff-defaults/) - Recommended rule selections
- [Python Typing Best Practices](https://typing.python.org/en/latest/reference/best_practices.html) - Official typing guidance

### Tertiary (LOW confidence)
- WebSearch results on rule recommendations - Community patterns, may vary

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official documentation confirms tool versions and usage
- Architecture: HIGH - Verified pyproject.toml patterns from official docs
- Pitfalls: HIGH - Common issues documented in official troubleshooting guides

**Research date:** 2026-02-03
**Valid until:** 2026-03-03 (30 days - Ruff is fast-moving but configuration is stable)
