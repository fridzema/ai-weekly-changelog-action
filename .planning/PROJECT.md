# AI Weekly Changelog Action

## What This Is

A GitHub Action that automatically generates weekly changelogs from repository commits using AI models via OpenRouter. The project is being polished for open source release as a portfolio piece — demonstrating professional engineering practices to potential employers while providing a useful tool for other developers.

## Core Value

**A working example of production-quality open source engineering** — green CI badge, comprehensive tests, clean code, and professional documentation.

## Requirements

### Validated

These capabilities already exist and work:

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

### Active

- [ ] Pytest test suite with 80%+ coverage on core logic
- [ ] Linting configuration (ruff) with pre-commit hooks
- [ ] CI pipeline running tests + linting on push/PR
- [ ] Green status badges visible in README
- [ ] Professional README with clear usage examples
- [ ] Fix bare `except: pass` blocks — use specific exceptions
- [ ] Fix silent language fallback — add warning when falling back
- [ ] Fix SECURITY.md placeholder email address
- [ ] Changelog validation before commit (valid markdown, links resolve)
- [ ] Better dry-run diff preview (show actual changes, not just first 100 lines)
- [ ] Configurable chunk size for cost/quality tradeoff
- [ ] API key redaction in all error paths

### Out of Scope

- Contribution workflow (CONTRIBUTING.md, PR templates, issue templates) — user didn't prioritize
- Mobile app or web UI — this is a CLI/CI tool
- Support for AI providers other than OpenRouter — existing architecture works
- Real-time notifications — batch changelog generation is the use case
- Changelog archival/rotation — defer to future if needed

## Context

**Current state:** Functional but unpolished. Zero tests, no linting, documentation has gaps. Code has some bare exception handling and silent fallbacks that hide errors.

**Codebase analysis:** Completed via `/gsd:map-codebase`. See `.planning/codebase/` for:
- TESTING.md — documents test gaps and recommended approach
- CONCERNS.md — lists tech debt, security issues, and fragile areas
- ARCHITECTURE.md — explains data flow and abstractions
- STACK.md — Python 3.11, OpenAI SDK, GitHub Actions

**Target audience:**
1. Potential employers evaluating engineering skill (code quality, tests, documentation)
2. Other developers who might use or contribute to the action

## Constraints

- **Tech stack**: Python 3.11+, GitHub Actions composite action — existing architecture, no major rewrites
- **API dependency**: OpenRouter via OpenAI SDK — must maintain compatibility
- **Test coverage target**: 80%+ on core logic (retry decorator, chunking, changelog writing)
- **CI requirement**: Tests and linting must pass for green badge

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use pytest for testing | Python standard, good fixture support | — Pending |
| Use ruff for linting | Fast, modern, replaces multiple tools | — Pending |
| Skip contribution workflow | User prioritized tests/docs over contributor experience | — Pending |
| Add changelog validation | Prevents broken markdown from being committed | — Pending |

---
*Last updated: 2026-02-03 after initialization*
