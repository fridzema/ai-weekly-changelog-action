# Technology Stack

**Analysis Date:** 2026-02-03

## Languages

**Primary:**
- Python 3.11 - AI changelog generation logic via `src/generate_changelog.py`
- Bash - Git operations, environment setup, and orchestration within GitHub Actions composite steps in `action.yml`
- YAML - GitHub Actions workflow configuration

**Secondary:**
- Markdown - Changelog output format (CHANGELOG.md)

## Runtime

**Environment:**
- GitHub Actions (composite action model)
- Linux/macOS/Windows compatible (uses `actions/checkout@v4`, `actions/setup-python@v4`)

**Package Manager:**
- pip (Python dependency manager)
- Lockfile: Not used (direct version pinning in requirements.txt)

## Frameworks

**Core:**
- OpenAI Python Client (`openai>=1.14,<2`) - Provides HTTP client for OpenRouter API integration in `src/generate_changelog.py:99-103`

**CI/CD:**
- GitHub Actions - Workflow orchestration via `action.yml` composite steps (checkout, Python setup, dependency installation, execution)

**Build/Dev:**
- Actions/Checkout@v4 - Repository checkout with dynamic fetch depth (100/300/500 commits based on `days_back`)
- Actions/Setup-Python@v4 - Python 3.11 environment setup
- git-auto-commit-action@v5 - Automated changelog commit

## Key Dependencies

**Critical:**
- `openai>=1.14,<2` - OpenRouter API client for AI-powered summary generation via HTTP POST to `https://openrouter.ai/api/v1/chat/completions`
- `requests` - HTTP library (referenced in requirements.txt but primarily used indirectly by openai client)

**Infrastructure:**
- None detected (serverless - runs on GitHub Actions runners)

## Configuration

**Environment:**
- Configured via GitHub Actions inputs in `action.yml` (lines 11-41):
  - `openrouter_api_key` (required) - API credentials
  - `days_back` (1-365, default: 7) - Lookback period validation
  - `model` (default: 'openai/gpt-5-mini') - LLM selection
  - `language` (default: 'English') - Output language (English, Dutch, German, French, Spanish)
  - `force` (default: false) - Override duplicate week entries
  - `extended` (default: false) - Detailed file analysis
  - `dry_run` (default: false) - Preview without commit

**Build:**
- `action.yml` - GitHub Action composite configuration with 8 execution steps
- Dynamic fetch depth in checkout (line 59): `${{ inputs.days_back <= 7 && 100 || (inputs.days_back <= 30 && 300 || 500) }}`

**Caching:**
- Local temporary cache at `/tmp/changelog_cache/` with key format: `{commit_hash}_{days_back}_{extended_mode}` (action.yml lines 81-86)
- Cache files: `*_commits.txt`, `*_extended.txt`, `*_files.txt`, `*.meta`
- Cache retention: Last 5 cache sets (older entries auto-cleaned)

## Platform Requirements

**Development:**
- Python 3.11+ (local testing)
- Git 2.0+ (commit history operations)
- bash shell

**Production:**
- GitHub Actions runner (ubuntu-latest recommended)
- GitHub repository with write permissions for changelog commits
- OpenRouter API account with active API key

## API Configuration

**OpenRouter Integration:**
- Base URL: `https://openrouter.ai/api/v1`
- Authentication: Bearer token via `OPENROUTER_API_KEY` environment variable
- Timeout: 30 seconds (OpenAI client initialization in `src/generate_changelog.py:99-103`)
- Extra headers: GitHub repository context for tracking:
  - `HTTP-Referer`: `https://github.com/{GITHUB_REPOSITORY}`
  - `X-Title`: `Weekly-Changelog-Generator`

---

*Stack analysis: 2026-02-03*
