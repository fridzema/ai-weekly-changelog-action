---
phase: 03
plan: 01
subsystem: quality-tooling
tags: [ruff, mypy, pip-audit, linting, type-checking, security]

dependency-graph:
  requires: []
  provides:
    - ruff-config
    - mypy-config
    - pip-audit-ready
  affects:
    - 03-02 (lint fixes)
    - 03-03 (type annotations)
    - 03-04 (security scanning)

tech-stack:
  added:
    - ruff@0.15.0
    - mypy@1.19.1
    - pip-audit@2.10.0
    - types-requests
  patterns: []

key-files:
  created: []
  modified:
    - pyproject.toml
    - requirements-dev.txt

decisions:
  - id: QUAL-01
    choice: "Ruff for linting AND formatting (replaces black, isort, flake8, etc.)"
    reason: "Single fast tool, modern, excellent Python 3.9+ support"
  - id: QUAL-02
    choice: "Enable flake8-bandit (S rules) for security scanning"
    reason: "Built into Ruff, covers common security issues"
  - id: QUAL-03
    choice: "Ignore errors in tests for mypy"
    reason: "Tests use mocking patterns that confuse type checker"
  - id: QUAL-04
    choice: "Allow assert in tests via per-file-ignores"
    reason: "S101 bandit rule warns about assert, but it's correct in tests"

metrics:
  duration: 1.5min
  completed: 2026-02-03
---

# Phase 03 Plan 01: Quality Tool Configuration Summary

**Ruff, mypy, pip-audit configured in pyproject.toml with dependencies in requirements-dev.txt**

## What Was Done

### Task 1: Add Ruff and mypy configuration to pyproject.toml

Added comprehensive tool configuration:

```toml
[tool.ruff]
target-version = "py39"
line-length = 88
exclude = [".venv", "build", "dist", ".git", "__pycache__"]

[tool.ruff.lint]
select = ["E", "W", "F", "I", "B", "S", "UP"]
ignore = ["E501"]

[tool.ruff.lint.per-file-ignores]
"tests/*" = ["S101"]  # Allow assert in tests

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
ignore_missing_imports = true
check_untyped_defs = true

[[tool.mypy.overrides]]
module = "tests.*"
ignore_errors = true
```

Commit: d1c7e34

### Task 2: Update requirements-dev.txt with quality tools

Added dependencies:
- ruff>=0.14.0
- mypy>=1.19
- pip-audit>=2.10.0
- types-requests

Commit: 0b8c8f8

### Task 3: Install and verify tools are available

All tools installed and verified:
- ruff 0.15.0
- mypy 1.19.1 (compiled: yes)
- pip-audit 2.10.0

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

All verification checks passed:
- pyproject.toml contains [tool.ruff], [tool.ruff.lint], [tool.ruff.format], [tool.mypy] sections
- requirements-dev.txt includes all quality tool dependencies
- All tools installed and executable from command line

## Rule Coverage

The enabled Ruff rules provide:

| Rule Set | Coverage |
|----------|----------|
| E (pycodestyle errors) | PEP 8 style violations |
| W (pycodestyle warnings) | PEP 8 style warnings |
| F (Pyflakes) | Logical errors, unused imports/variables |
| I (isort) | Import ordering and organization |
| B (flake8-bugbear) | Common bugs and design problems |
| S (flake8-bandit) | Security vulnerabilities |
| UP (pyupgrade) | Python version upgrades |

## Next Phase Readiness

Ready for 03-02: Apply Ruff fixes to codebase

Tools are configured and installed. Next plan will:
1. Run `ruff check --fix` to auto-fix linting issues
2. Run `ruff format` to apply consistent formatting
3. Address any remaining manual fixes
