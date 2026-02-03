# Technology Stack: Python Testing, Linting & CI

**Project:** AI Weekly Changelog Action
**Target:** Open source Python GitHub Action polish
**Python Version:** 3.11 (existing)
**Researched:** 2026-02-03

## Executive Summary

For a 2026 Python GitHub Action, the optimal stack is **Ruff + pytest + pre-commit + pip-audit + GitHub Actions**. This represents the modern Python tooling consensus: Ruff has replaced the multi-tool chaos of Black/Flake8/isort, pytest remains dominant for testing, and pip-audit provides free dependency scanning suitable for open source projects.

**Key principle:** Minimize dependencies while maximizing coverage and speed. This action already has only 2 runtime dependencies (openai, requests) - keep the dev tooling equally lean.

---

## Recommended Stack

### Testing Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **pytest** | `>=9.0.2` | Test framework | Industry standard with superior fixtures, plugins, and DX. 30x adoption over unittest in modern projects. Clean syntax with plain asserts. |
| **pytest-cov** | `>=6.3` | Coverage reporting | Integrates coverage.py 7.13+ with pytest. Enables branch coverage, xdist support, and CI integration. |
| **coverage[toml]** | `>=7.13.2` | Coverage engine | Required by pytest-cov. Supports Python 3.10-3.15. TOML config in pyproject.toml. |

**Rationale:**
- **pytest over unittest**: Despite unittest being stdlib, pytest's fixture system, plugin ecosystem, and readability make it the 2026 standard. Every source confirms pytest dominance.
- **pytest-cov over running coverage directly**: Automatic management of .coverage files, xdist support for parallel testing, and better CI integration. Coverage.py docs acknowledge most users want pytest-cov despite not being "necessary."
- **Target: 80%+ coverage** as specified in requirements.

**Confidence:** HIGH (verified with [pytest releases](https://docs.pytest.org/en/stable/changelog.html), [pytest-cov PyPI](https://pypi.org/project/pytest-cov/), [coverage.py docs](https://coverage.readthedocs.io/))

---

### Linting & Formatting

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **Ruff** | `>=0.14.14` | Linter + formatter | Replaces Black, Flake8, isort, pyupgrade, and 10+ other tools. 100x faster than alternatives. 99.9% Black-compatible. Written in Rust. Used by pandas, FastAPI, Apache Airflow. |

**Rationale:**
- **Ruff replaces everything**: In 2026, running separate Black + Flake8 + isort is legacy. Ruff provides linting (800+ rules) and formatting in one tool.
- **Speed matters for CI**: Ruff is 100x faster than Flake8, meaning sub-second linting even on large codebases.
- **Black compatibility**: Projects migrating from Black can use Ruff's formatter as a drop-in replacement.
- **DO NOT use**: Black (superseded by Ruff), Flake8 (superseded by Ruff), isort (superseded by Ruff), pylint (too slow, too noisy).

**Configuration:** Use `pyproject.toml` for all Ruff settings (supports both linter and formatter config).

**Confidence:** HIGH (verified with [Ruff releases](https://github.com/astral-sh/ruff/releases), [Ruff docs](https://docs.astral.sh/ruff/), [adoption evidence](https://astral.sh/blog/the-ruff-formatter))

---

### Type Checking (Optional but Recommended)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **mypy** | `>=1.19.1` | Static type checker | Industry standard for Python type checking. Supports Python 3.9+. Incremental adoption friendly. |

**Rationale:**
- **Mypy remains standard**: Despite new competitor `ty` from Astral (Ruff creators), mypy is still the 2026 type checking standard.
- **Portfolio value**: Demonstrating type hints + mypy shows professional Python practices.
- **Incremental adoption**: Can start with loose settings and tighten over time.
- **Alternative:** `ty` is emerging but too new (2026) for production recommendation.

**Configuration:** Start with basic settings in `pyproject.toml`, can enable `--strict` mode for maximum safety.

**Confidence:** MEDIUM-HIGH (mypy verified via [PyPI](https://pypi.org/project/mypy/) and [docs](https://mypy.readthedocs.io/); ty is emerging alternative mentioned in [2026 sources](https://www.blog.pythonlibrary.org/2026/01/09/how-to-switch-to-ty-from-mypy/))

---

### Security Scanning

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **bandit** | `>=1.9.3` | SAST security scanner | Scans Python code for common security issues. Industry standard, maintained by PyCQA. 1.6M+ weekly downloads. |
| **pip-audit** | `latest` | Dependency vulnerability scanner | Free, Google-backed, no subscription required. Uses PyPI Advisory Database. Can auto-fix with `--fix`. |

**Rationale:**
- **bandit for code scanning**: Catches hardcoded passwords, SQL injection, unsafe YAML loading, etc. Essential for security-conscious open source.
- **pip-audit over Safety**: Safety requires paid license for commercial use ($25/seat/mo). pip-audit is fully free and OSS-appropriate. Both scan PyPI vulnerabilities, but pip-audit is transparent and community-backed.
- **DO NOT use**: `safety` (commercial licensing conflicts with open source), proprietary scanners (overkill for GitHub Action).

**Configuration:** bandit config in `pyproject.toml` or `.bandit` file. pip-audit runs in CI without config.

**Confidence:** HIGH (verified with [bandit release](https://www.helpnetsecurity.com/2026/01/21/bandit-open-source-tool-find-security-issues-python-code/), [pip-audit comparison](https://www.sixfeetup.com/blog/safety-pip-audit-python-security-tools))

---

### Pre-commit Hooks

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **pre-commit** | `>=4.0.0` | Git hook manager | Industry standard for managing pre-commit hooks. Ensures code quality before commits enter history. |

**Hook Configuration:**
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v6.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-added-large-files
      - id: check-ast
      - id: debug-statements

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.14
    hooks:
      - id: ruff        # Linter
        args: [--fix]
      - id: ruff-format # Formatter

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.19.1
    hooks:
      - id: mypy
        additional_dependencies: [types-requests]
```

**Rationale:**
- **Ruff in pre-commit**: Runs linting + formatting before commit, catches issues locally.
- **Standard hooks**: Trailing whitespace, file endings, YAML validation are table-stakes.
- **Fast execution**: Ruff's speed means pre-commit hooks run in <1s typically.

**Confidence:** HIGH (verified with [pre-commit docs](https://pre-commit.com/), [pre-commit hooks v6.0.0](https://github.com/pre-commit/pre-commit-hooks))

---

### CI/CD (GitHub Actions)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| **GitHub Actions** | N/A (platform) | CI/CD platform | Native integration with GitHub. Free for public repos. Matrix builds for multi-version testing. |
| **actions/checkout** | `@v4` | Repository checkout | Standard action for checking out code. |
| **actions/setup-python** | `@v5` | Python installation | Installs Python with version matrix support. |
| **codecov/codecov-action** | `@v5` | Coverage upload | Free for open source. Superior UI and PR integration vs Coveralls. |

**GitHub Actions Workflow Strategy:**

```yaml
name: Test & Lint

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13"]

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Lint with Ruff
        run: |
          ruff check .
          ruff format --check .

      - name: Type check with mypy
        run: mypy src/

      - name: Security scan with bandit
        run: bandit -r src/ -c pyproject.toml

      - name: Dependency audit
        run: pip-audit

      - name: Test with pytest
        run: pytest --cov=src --cov-report=xml --cov-report=term

      - name: Upload coverage
        if: matrix.python-version == '3.11'
        uses: codecov/codecov-action@v5
        with:
          file: ./coverage.xml
```

**Rationale:**
- **Matrix testing**: Test across Python 3.10-3.13 to ensure compatibility (GitHub Actions supports this natively).
- **Pip caching**: `actions/setup-python` with `cache: 'pip'` speeds up installs (though this action has only 2 deps, so less critical).
- **Codecov over Coveralls**: Better UI, better PR integration, equally free for OSS. Industry preference in 2026.
- **Run security scans in CI**: Ensures every PR is scanned for vulnerabilities.

**Confidence:** HIGH (verified with [GitHub Actions Python guide](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python), [Codecov docs](https://about.codecov.io/blog/python-code-coverage-using-github-actions-and-codecov/))

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Testing | pytest | unittest | Stdlib but inferior DX, verbose, limited fixtures |
| Testing | pytest | Robot Framework | Overkill for unit testing, better for acceptance tests |
| Formatting | Ruff | Black | Ruff is Black-compatible but 30x faster + includes linting |
| Linting | Ruff | Flake8 | Ruff is 100x faster + more comprehensive rules |
| Linting | Ruff | pylint | Too slow, too opinionated, high false positive rate |
| Type checking | mypy | ty | Too new (2026), insufficient adoption data |
| Multi-version testing | GitHub Actions matrix | tox | Unnecessary complexity for CI; GitHub matrix is simpler |
| Multi-version testing | N/A | nox | Adds dependency; GitHub Actions handles this natively |
| Dependency scanning | pip-audit | safety | Safety requires commercial license ($25/seat) |
| Coverage hosting | Codecov | Coveralls | Codecov has better UI and PR integration |

---

## Installation

**pyproject.toml (recommended):**

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "ai-weekly-changelog-action"
version = "1.0.0"
requires-python = ">=3.10"
dependencies = [
    "openai>=1.14,<2",
    "requests",
]

[project.optional-dependencies]
dev = [
    "pytest>=9.0.2",
    "pytest-cov>=6.3",
    "coverage[toml]>=7.13.2",
    "ruff>=0.14.14",
    "mypy>=1.19.1",
    "types-requests",
    "bandit[toml]>=1.9.3",
    "pip-audit",
    "pre-commit>=4.0.0",
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
    "--cov-branch",
    "--strict-markers",
]

[tool.coverage.run]
source = ["src"]
branch = true
omit = ["tests/*", "**/__pycache__/*"]

[tool.coverage.report]
precision = 2
show_missing = true
fail_under = 80.0

[tool.ruff]
line-length = 120
target-version = "py310"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = []

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false  # Start permissive, tighten later
strict_optional = true

[tool.bandit]
exclude_dirs = ["tests", "venv"]
skips = ["B101"]  # Skip assert_used in tests
```

**Installation commands:**

```bash
# Install runtime dependencies
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"

# Setup pre-commit hooks
pre-commit install

# Run all checks manually
pre-commit run --all-files
```

---

## Migration Path (from current state)

Current state analysis:
- ✅ Python 3.11 in use
- ✅ Minimal runtime dependencies (openai, requests)
- ❌ No testing framework
- ❌ No linting/formatting
- ❌ No pre-commit hooks
- ❌ No CI beyond basic usage examples

**Recommended implementation order:**

1. **Phase 1: Testing foundation**
   - Add pytest + pytest-cov
   - Create `tests/` directory structure
   - Write first tests (start with simple utility functions)
   - Achieve 50% coverage baseline

2. **Phase 2: Code quality tooling**
   - Add Ruff for linting + formatting
   - Format entire codebase with `ruff format`
   - Fix linting issues with `ruff check --fix`
   - Add pyproject.toml configuration

3. **Phase 3: Pre-commit + security**
   - Setup pre-commit hooks
   - Add bandit security scanning
   - Add pip-audit dependency scanning
   - Run `pre-commit run --all-files` to ensure passing

4. **Phase 4: CI pipeline**
   - Create `.github/workflows/test.yml`
   - Enable matrix testing (Python 3.10-3.13)
   - Add Codecov integration
   - Enforce checks on PRs

5. **Phase 5: Type checking (stretch goal)**
   - Add mypy
   - Add type hints incrementally
   - Enable stricter mypy settings over time

**Estimated effort:** 3-5 days for Phases 1-4 (80% coverage + full CI). Phase 5 is ongoing/incremental.

---

## Dependencies Summary

**Runtime (existing):**
```
openai>=1.14,<2
requests
```

**Development (new):**
```
pytest>=9.0.2
pytest-cov>=6.3
coverage[toml]>=7.13.2
ruff>=0.14.14
mypy>=1.19.1
types-requests
bandit[toml]>=1.9.3
pip-audit
pre-commit>=4.0.0
```

**Total new dependencies:** 9 packages (but Ruff replaces what would have been 5-6 separate tools)

---

## Sources

### Testing Framework
- [pytest documentation](https://docs.pytest.org/en/stable/)
- [pytest changelog - confirms v9.0.2 latest](https://docs.pytest.org/en/stable/changelog.html)
- [pytest vs unittest comparison](https://pytest-with-eric.com/comparisons/pytest-vs-unittest/)
- [pytest-cov PyPI](https://pypi.org/project/pytest-cov/)
- [coverage.py documentation](https://coverage.readthedocs.io/)
- [Python testing best practices 2026](https://testgrid.io/blog/python-testing-framework/)

### Linting & Formatting
- [Ruff GitHub releases](https://github.com/astral-sh/ruff/releases)
- [Ruff formatter announcement](https://astral.sh/blog/the-ruff-formatter)
- [Ruff vs Black comparison](https://www.getorchestra.io/guides/ruff-vs-black-formatter-linting-and-formatting-in-vscode)
- [Why replace Flake8, Black, and isort with Ruff](https://medium.com/@zigtecx/why-you-should-replace-flake8-black-and-isort-with-ruff-the-ultimate-python-code-quality-tool-a9372d1ddc1e)

### Type Checking
- [mypy documentation](https://mypy.readthedocs.io/)
- [mypy PyPI - confirms v1.19.1](https://pypi.org/project/mypy/)
- [ty from mypy comparison (emerging alternative)](https://www.blog.pythonlibrary.org/2026/01/09/how-to-switch-to-ty-from-mypy/)

### Security Scanning
- [bandit 1.9.3 release announcement](https://www.helpnetsecurity.com/2026/01/21/bandit-open-source-tool-find-security-issues-python-code/)
- [bandit GitHub](https://github.com/PyCQA/bandit)
- [pip-audit GitHub](https://github.com/pypa/pip-audit)
- [Safety vs pip-audit comparison](https://www.sixfeetup.com/blog/safety-pip-audit-python-security-tools)

### Pre-commit Hooks
- [pre-commit official docs](https://pre-commit.com/)
- [pre-commit hooks v6.0.0](https://github.com/pre-commit/pre-commit-hooks)
- [pre-commit setup guide](https://stefaniemolin.com/articles/devx/pre-commit/setup-guide/)

### CI/CD & GitHub Actions
- [GitHub Actions Python guide](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)
- [GitHub Actions best practices 2026](https://medium.com/hydroinformatics/the-ultimate-guide-to-python-ci-cd-mastering-github-actions-composite-actions-for-modern-python-0d7730c17b9e)
- [Codecov Python integration](https://about.codecov.io/blog/python-code-coverage-using-github-actions-and-codecov/)
- [Codecov vs Coveralls comparison](https://stackshare.io/stackups/codecov-vs-coveralls)

---

## Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Testing (pytest) | HIGH | Verified via official docs, PyPI, and multiple 2026 sources confirming v9.0.2 and industry dominance |
| Linting/Formatting (Ruff) | HIGH | Verified via GitHub releases (0.14.14), adoption by major projects (pandas, FastAPI), and comparative analyses |
| Type Checking (mypy) | MEDIUM-HIGH | Verified via PyPI and docs; marked medium due to emerging `ty` alternative, but mypy still standard |
| Security (bandit) | HIGH | Verified via 2026 release announcement, PyCQA maintenance, download statistics |
| Security (pip-audit) | HIGH | Verified via comparison articles and official GitHub; clear licensing advantage over Safety |
| Pre-commit | HIGH | Verified via official docs and hook repository versions |
| GitHub Actions | HIGH | Verified via official GitHub documentation and CI/CD best practices articles |

**Overall Stack Confidence: HIGH**

All recommendations based on 2026-current sources, version numbers verified, and alternatives explicitly considered and rejected with rationale.
