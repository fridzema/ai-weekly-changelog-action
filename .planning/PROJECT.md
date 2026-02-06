# AI Weekly Changelog Action

## What This Is

A GitHub Action that automatically generates weekly changelogs from repository commits using AI models via OpenRouter. This polished open source project serves as a portfolio piece demonstrating production-quality engineering practices — comprehensive testing, modern tooling, automated CI/CD, and professional documentation.

## Core Value

**A working example of production-quality open source engineering** — green CI badge, comprehensive tests, clean code, and professional documentation.

## Requirements

### Validated

**Core functionality (existing):**
- ✓ AI-powered changelog generation from git commits — existing
- ✓ Multi-language support (English, Dutch, German, French, Spanish) — existing
- ✓ Micro-chunking for large commit sets (5 commits/chunk) — existing
- ✓ Retry logic with exponential backoff and rate-limit awareness — existing
- ✓ File-based caching with automatic cleanup — existing
- ✓ Dry-run mode for preview without commit — existing
- ✓ Force update to overwrite existing week entries — existing
- ✓ Extended analysis mode with file statistics — existing
- ✓ Dynamic git fetch depth based on lookback period — existing
- ✓ GitHub Actions composite action packaging — existing

**Quality improvements (v1.0):**
- ✓ Pytest test suite with 91% coverage — v1.0
- ✓ Ruff linting + formatting with zero errors — v1.0
- ✓ mypy type checking on all public functions — v1.0
- ✓ pip-audit security scanning with no vulnerabilities — v1.0
- ✓ GitHub Actions CI/CD with 4 parallel jobs — v1.0
- ✓ CI and License status badges in README — v1.0
- ✓ Professional README with quick start and troubleshooting — v1.0
- ✓ Specific exception handling (replaced bare except blocks) — v1.0
- ✓ Language fallback warnings (no silent failures) — v1.0
- ✓ SECURITY.md with GitHub Security Advisories contact — v1.0
- ✓ CODE_OF_CONDUCT.md with Contributor Covenant v2.1 — v1.0
- ✓ Architecture documentation with 7 Mermaid diagrams — v1.0
- ✓ API key redaction across all error paths — v1.0

### Active

(Next milestone requirements will be defined with `/gsd:new-milestone`)

### Out of Scope

- Contribution workflow (CONTRIBUTING.md, PR templates, issue templates) — user prioritized quality over contributor process, CODE_OF_CONDUCT covers basics
- Mobile app or web UI — this is a CI/CD tool, GitHub Actions is the interface
- Support for AI providers other than OpenRouter — OpenRouter already provides multi-model access
- Real-time notifications — batch changelog generation (weekly) is the core use case
- Changelog archival/rotation — CHANGELOG.md append-only structure works well, no rotation needed

## Context

**Current state (v1.0 shipped):** Production-quality open source project with 91% test coverage, zero linting/type errors, automated CI/CD, and professional documentation. Ready for portfolio presentation and real-world use.

**Shipped:** 2,039 lines Python, 61 tests, 56 files modified over 3 days (Feb 3-6, 2026).

**Tech stack:** Python 3.11+, OpenAI SDK, GitHub Actions composite action, pytest, Ruff, mypy, pip-audit.

**Quality metrics:**
- Test coverage: 91% (target: 80%)
- Linting: 0 errors (Ruff)
- Type checking: 0 errors (mypy)
- Security: 0 vulnerabilities (pip-audit)
- CI/CD: 4 parallel jobs (lint, test, type-check, security)

**Target audience:**
1. Potential employers evaluating engineering skill (demonstrated through systematic quality improvements)
2. Other developers who need AI-powered changelog generation for their projects

## Constraints

- **Tech stack**: Python 3.11+, GitHub Actions composite action — existing architecture, no major rewrites
- **API dependency**: OpenRouter via OpenAI SDK — must maintain compatibility
- **Test coverage target**: 80%+ on core logic (retry decorator, chunking, changelog writing)
- **CI requirement**: Tests and linting must pass for green badge

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use pytest for testing | Python standard, good fixture support | ✓ Good - 61 tests, 91% coverage |
| Use ruff for linting | Fast, modern, replaces multiple tools | ✓ Good - replaced black, isort, flake8 |
| Use mypy for type checking | Industry standard, catches type errors | ✓ Good - found Optional handling issues |
| Use pip-audit for security | Official Python security scanner | ✓ Good - zero vulnerabilities |
| Skip contribution workflow | User prioritized tests/docs over contributor experience | ✓ Good - CODE_OF_CONDUCT covers basics |
| Use GitHub Security Advisories for contact | Modern private vulnerability reporting | ✓ Good - no email maintenance needed |
| 7 focused Mermaid diagrams vs 1-2 large | Easier to understand individual concepts | ✓ Good - better comprehension |
| Micro-chunking (5 commits/chunk) | Detailed analysis quality over API cost | — Validated in production use |
| OSError for file operations | Covers all I/O errors consistently | ✓ Good - cleaner error handling |
| Dual API key redaction strategy | Exact match + regex for comprehensive protection | ✓ Good - caught edge cases in tests |
| Extract nested functions for testability | process_commits_in_chunks, get_language_config | ✓ Good - enabled proper unit testing |
| 80% coverage threshold | Standard Python quality bar, achievable | ✓ Good - exceeded at 91% |

---
*Last updated: 2026-02-06 after v1.0 milestone*
