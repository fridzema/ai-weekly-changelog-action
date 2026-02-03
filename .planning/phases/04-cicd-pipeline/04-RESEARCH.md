# Phase 4: CI/CD Pipeline - Research

**Researched:** 2026-02-03
**Domain:** GitHub Actions CI/CD workflows for Python projects
**Confidence:** HIGH

## Summary

Phase 4 implements automated CI/CD using GitHub Actions to run the quality tools configured in Phase 3 (pytest, ruff, mypy, pip-audit) on every push and pull request. The project already has three workflows (auto-latest.yml, example-full.yml, example-simple.yml) but lacks a dedicated CI workflow for running quality checks.

The standard pattern for Python CI in GitHub Actions is to use separate parallel jobs for linting, testing, and security scanning. This provides faster feedback (jobs run simultaneously), clearer failure identification, and follows GitHub's recommended CI architecture. The `actions/setup-python@v5` action with built-in pip caching reduces setup time, while Ruff's `--output-format=github` enables inline annotations on pull requests.

**Primary recommendation:** Create a single `.github/workflows/ci.yml` workflow with parallel jobs for lint, test, type-check, and security-audit. Use `actions/setup-python@v5` with `cache: 'pip'` and `astral-sh/ruff-action@v3` for optimal performance. Add a status badge to README referencing the workflow file name.

## Standard Stack

The established tools and actions for Python CI in GitHub Actions:

### Core Actions

| Action | Version | Purpose | Why Standard |
|--------|---------|---------|--------------|
| actions/checkout | v4 | Clone repository | Official GitHub action, required for all CI |
| actions/setup-python | v5 | Install Python with caching | Official, built-in pip/pipenv/poetry caching |
| astral-sh/ruff-action | v3 | Run Ruff linting/formatting | Official Ruff action, adds to PATH, fast installation |
| pypa/gh-action-pip-audit | v1.1.0 | Dependency vulnerability scanning | Official PyPA action, integrates with GitHub summaries |

### Supporting Actions

| Action | Version | Purpose | When to Use |
|--------|---------|---------|-------------|
| actions/cache | v4 | Custom caching | Only if setup-python caching insufficient |
| actions/upload-artifact | v4 | Store build artifacts | For coverage reports, test results |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| astral-sh/ruff-action | pipx install ruff | ruff-action is faster, auto-version detection from pyproject.toml |
| pypa/gh-action-pip-audit | pip install pip-audit && pip-audit | Action provides better GitHub integration, summary output |
| Separate parallel jobs | Single combined job | Parallel is faster for feedback but uses more runner minutes |

**Installation in workflow:**
```yaml
# No additional installation needed - actions handle tool installation
# requirements-dev.txt already has: ruff>=0.14.0, mypy>=1.19, pip-audit>=2.10.0
```

## Architecture Patterns

### Recommended Workflow Structure

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/ruff-action@v3
        with:
          args: "check --output-format=github"
      - uses: astral-sh/ruff-action@v3
        with:
          args: "format --check --diff"

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
          cache-dependency-path: |
            requirements.txt
            requirements-dev.txt
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest tests/ --cov=src --cov-report=xml --cov-report=term-missing

  type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      - run: pip install mypy types-requests
      - run: mypy src/

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - uses: pypa/gh-action-pip-audit@v1.1.0
```

### Pattern 1: Parallel Jobs for Fast Feedback

**What:** Run lint, test, type-check, and security as separate parallel jobs
**When to use:** Default for all CI - provides fastest feedback
**Example:**
```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    # ... lint steps
  test:
    runs-on: ubuntu-latest
    # ... test steps (runs in parallel with lint)
  type-check:
    runs-on: ubuntu-latest
    # ... mypy steps (runs in parallel)
  security:
    runs-on: ubuntu-latest
    # ... pip-audit steps (runs in parallel)
```
**Benefit:** If linting fails, you know immediately while tests are still running.

### Pattern 2: Ruff with GitHub Annotations

**What:** Use `--output-format=github` for inline PR annotations
**When to use:** Always for ruff check in CI
**Example:**
```yaml
- uses: astral-sh/ruff-action@v3
  with:
    args: "check --output-format=github src/ tests/"
```
**Benefit:** Lint errors appear as inline comments on changed lines in PR diffs.

### Pattern 3: Cache Pip Dependencies

**What:** Use setup-python's built-in caching with multiple dependency files
**When to use:** Always - reduces install time by 30-60 seconds
**Example:**
```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.11'
    cache: 'pip'
    cache-dependency-path: |
      requirements.txt
      requirements-dev.txt
```

### Pattern 4: Status Badge in README

**What:** Add clickable CI status badge at top of README
**When to use:** After CI workflow is created and passing
**Example:**
```markdown
[![CI](https://github.com/fridzema/ai-weekly-changelog-action/actions/workflows/ci.yml/badge.svg)](https://github.com/fridzema/ai-weekly-changelog-action/actions/workflows/ci.yml)
```
**Note:** Use workflow FILE name (`ci.yml`), not display name.

### Anti-Patterns to Avoid

- **Running all checks sequentially in one job:** Wastes time - checks can run in parallel
- **Not using setup-python caching:** Each job reinstalls dependencies from scratch
- **Using `continue-on-error: true` on required checks:** Masks failures, defeats CI purpose
- **Installing ruff via pip when using ruff-action:** Redundant, ruff-action handles installation
- **Hardcoding Python version in multiple places:** Use strategy matrix or consistent version

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Ruff installation | pip install in each job | astral-sh/ruff-action@v3 | Faster binary download, auto-version from pyproject.toml |
| Pip caching | actions/cache with pip cache dir | setup-python cache: 'pip' | Built-in, handles cache invalidation automatically |
| pip-audit GitHub integration | pip-audit --format json | pypa/gh-action-pip-audit | Automatic job summaries, proper exit codes |
| Status badge URL construction | Manual URL building | GitHub UI "Create status badge" | Ensures correct format, branch parameters |

**Key insight:** GitHub Actions ecosystem has mature, official actions for common Python CI tasks. Using official actions ensures compatibility with GitHub's evolving features and security practices.

## Common Pitfalls

### Pitfall 1: Wrong Workflow File Reference in Badge

**What goes wrong:** Badge shows "no status" or wrong workflow
**Why it happens:** Using display name instead of file name in badge URL
**How to avoid:** Always use file name: `workflows/ci.yml/badge.svg`, not `workflows/CI/badge.svg`
**Warning signs:** Badge shows "no status" despite passing workflows

### Pitfall 2: Cache Not Working Across Jobs

**What goes wrong:** Each parallel job reinstalls all dependencies
**Why it happens:** GitHub Actions jobs run on separate runners; cache is per-runner
**How to avoid:** This is expected behavior - accept it or use a single job
**Warning signs:** Install step takes same time in all jobs despite caching

### Pitfall 3: pip-audit Fails on Unpinned Dependencies

**What goes wrong:** pip-audit can't resolve flexible version specifiers
**Why it happens:** `>=1.0` style requirements need resolution before auditing
**How to avoid:** Install dependencies first, then audit environment (not requirements file)
**Warning signs:** Error messages about version specifiers or dependency resolution

### Pitfall 4: mypy Fails on Missing Type Stubs

**What goes wrong:** mypy errors on third-party imports
**Why it happens:** Libraries without type stubs or inline types
**How to avoid:** Use `ignore_missing_imports = true` (already configured in Phase 3)
**Warning signs:** Errors about "Cannot find implementation or library stub"

### Pitfall 5: Ruff Action Version Mismatch

**What goes wrong:** CI uses different ruff version than local development
**Why it happens:** ruff-action defaults to latest, local may be pinned
**How to avoid:** Pin version in action: `version: "0.14.0"` or use `version-file: "pyproject.toml"`
**Warning signs:** CI passes/fails differently than local `ruff check`

### Pitfall 6: Branch Filter Missing for Main Protection

**What goes wrong:** CI runs on all branches including feature branches
**Why it happens:** Missing `branches: [main]` filter on push event
**How to avoid:** Add explicit branch filter: `push: branches: [main]`
**Warning signs:** CI runs multiple times per PR (on PR + on feature branch push)

## Code Examples

Verified patterns from official sources:

### Complete CI Workflow for This Project

```yaml
# Source: GitHub Docs + Official Action READMEs
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    name: Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Ruff linting
        uses: astral-sh/ruff-action@v3
        with:
          args: "check --output-format=github src/ tests/"

      - name: Check Ruff formatting
        uses: astral-sh/ruff-action@v3
        with:
          args: "format --check --diff src/ tests/"

  test:
    name: Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
          cache-dependency-path: |
            requirements.txt
            requirements-dev.txt

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt -r requirements-dev.txt

      - name: Run tests with coverage
        run: pytest tests/ -v --cov=src --cov-report=term-missing --cov-fail-under=80

  type-check:
    name: Type Check
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
          cache-dependency-path: requirements-dev.txt

      - name: Install mypy
        run: pip install mypy types-requests

      - name: Run mypy
        run: mypy src/

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt -r requirements-dev.txt

      - name: Run pip-audit
        uses: pypa/gh-action-pip-audit@v1.1.0
```

### Status Badge Markdown

```markdown
<!-- Source: GitHub Docs - Adding a workflow status badge -->
[![CI](https://github.com/fridzema/ai-weekly-changelog-action/actions/workflows/ci.yml/badge.svg)](https://github.com/fridzema/ai-weekly-changelog-action/actions/workflows/ci.yml)
```

### Badge with Branch Filter

```markdown
<!-- Show status for main branch only -->
[![CI](https://github.com/fridzema/ai-weekly-changelog-action/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/fridzema/ai-weekly-changelog-action/actions/workflows/ci.yml)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| pip install ruff in workflow | astral-sh/ruff-action@v3 | 2024 | Faster, automatic version detection |
| actions/cache for pip | setup-python cache: 'pip' | 2021 | Simpler, built-in handling |
| Separate bandit action | Ruff S rules | 2024 | Faster, integrated (Phase 3 decision) |
| Manual pip-audit command | pypa/gh-action-pip-audit@v1 | 2023 | Better GitHub integration |
| Single workflow file name | Multiple specific workflows | 2023-2024 | ci.yml for CI, release.yml for CD |

**Deprecated/outdated:**
- `actions/setup-python@v4`: Use v5 for node20 runtime
- `actions/checkout@v3`: Use v4 for node20 runtime
- Manual pip cache with actions/cache: Use setup-python built-in caching
- `--format=github` (old ruff flag): Use `--output-format=github`

## Open Questions

Things that couldn't be fully resolved:

1. **Optimal Python version for CI**
   - What we know: Project supports Python 3.9+ (pyproject.toml target-version)
   - What's unclear: Whether to test on 3.9 (minimum) or 3.11 (latest stable)
   - Recommendation: Use 3.11 for single-version CI; add matrix later if needed

2. **Coverage upload to external service**
   - What we know: pytest-cov generates reports; many services exist (Codecov, Coveralls)
   - What's unclear: Whether coverage badge is required for Phase 4 (not in requirements)
   - Recommendation: Skip for now; add in Phase 5 if needed for "professional presentation"

3. **Required vs informational checks**
   - What we know: GitHub can require certain checks to pass before merging
   - What's unclear: Whether branch protection should be configured as part of Phase 4
   - Recommendation: Focus on workflow creation; branch protection is repo settings, not code

## Sources

### Primary (HIGH confidence)
- [GitHub Docs: Building and testing Python](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python) - Official Python CI guide
- [GitHub Docs: Adding a workflow status badge](https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/monitoring-workflows/adding-a-workflow-status-badge) - Badge URL format
- [actions/setup-python](https://github.com/actions/setup-python) - Official action with caching documentation
- [astral-sh/ruff-action](https://github.com/astral-sh/ruff-action) - Official Ruff action with args/version options
- [pypa/gh-action-pip-audit](https://github.com/pypa/gh-action-pip-audit) - Official PyPA pip-audit action

### Secondary (MEDIUM confidence)
- [Ruff Integrations](https://docs.astral.sh/ruff/integrations/) - GitHub Actions integration patterns
- [Real Python: GitHub Actions Python](https://realpython.com/github-actions-python/) - Comprehensive CI patterns
- [Sourcery: GitHub Actions for Python](https://sourcery.ai/blog/github-actions) - Best practices guide

### Tertiary (LOW confidence)
- WebSearch results on parallel vs single job - Community patterns, varies by project size

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Official GitHub and tool documentation confirms action versions
- Architecture: HIGH - Verified patterns from official sources
- Pitfalls: HIGH - Common issues documented in official troubleshooting guides

**Research date:** 2026-02-03
**Valid until:** 2026-03-03 (30 days - GitHub Actions ecosystem is stable)
