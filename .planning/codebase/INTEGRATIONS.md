# External Integrations

**Analysis Date:** 2026-02-03

## APIs & External Services

**AI/LLM Services:**
- OpenRouter (https://openrouter.ai) - AI-powered changelog generation
  - SDK/Client: `openai>=1.14,<2` (Python package)
  - Auth: Environment variable `OPENROUTER_API_KEY`
  - Base URL: `https://openrouter.ai/api/v1`
  - Usage: Chat completions API at `/v1/chat/completions` for technical and business summaries
  - Models supported: Any OpenRouter model (defaults to `openai/gpt-5-mini`)
  - Implementation: `src/generate_changelog.py:99-103` (client initialization), lines 517-529 (API calls)

## Data Storage

**Databases:**
- None - Stateless changelog generation

**File Storage:**
- Local filesystem only - Changelog written to `CHANGELOG.md` in repository root
- Temporary cache: `/tmp/changelog_cache/` with time-based cleanup

**Caching:**
- OpenRouter API - No caching strategy (each API call is fresh)
- Local cache of git operations results (commit hashes, stats) in `/tmp/changelog_cache/` (action.yml lines 81-104)

## Authentication & Identity

**Auth Provider:**
- None - OpenRouter API key passed directly as bearer token
  - Key format validation: Must start with `sk-or-` prefix (src/generate_changelog.py:94-96)
  - Stored as GitHub Actions secret: `OPENROUTER_API_KEY`
  - Passed to action via input parameter in workflow (action.yml line 11-12)

**API Key Management:**
- Required: GitHub repository Settings > Secrets and variables > Actions
- Secret name: `OPENROUTER_API_KEY`
- Source: https://openrouter.ai/keys

## Monitoring & Observability

**Error Tracking:**
- None - Errors output to GitHub Actions step logs

**Logs:**
- GitHub Actions step summary output
- Detailed debugging via inline bash `echo` statements in action.yml (lines 74-78, 108-198)
- Progress indicators for large commit sets (src/generate_changelog.py:295-296, 567, 387-389)

**Dry Run Mode:**
- Outputs changelog preview to GitHub Actions step summary instead of committing (action.yml lines 259-273)

## CI/CD & Deployment

**Hosting:**
- GitHub Actions (serverless)
- Runs on ubuntu-latest (or user-specified GitHub Actions runner)

**CI Pipeline:**
- GitHub Actions composite action model (action.yml)
- Execution steps:
  1. Input validation (days_back: 1-365 range)
  2. Repository checkout with dynamic fetch depth
  3. Git commit collection and extended analysis (optional parallel operations)
  4. Python 3.11 environment setup
  5. Dependency installation (pip install openai requests)
  6. Changelog generation (Python script execution)
  7. Week metadata calculation
  8. Auto-commit via stefanzweifel/git-auto-commit-action@v5

**Commit Details:**
- Committer: github-actions[bot]
- Email: 41898282+github-actions[bot]@users.noreply.github.com
- Message format: `docs: update weekly changelog (week {week_num}, {year})[, {forced update suffix}]`

## Environment Configuration

**Required env vars:**
- `OPENROUTER_API_KEY` - API authentication (from GitHub Actions secret)
- `GITHUB_REPOSITORY` - Used for commit links in changelog and API headers (auto-provided by GitHub)

**Optional env vars (from action inputs):**
- `GITHUB_TOKEN` - DEPRECATED (auto-provided by GitHub)
- `MODEL` - OpenRouter model name (default: openai/gpt-5-mini)
- `OUTPUT_LANGUAGE` - Changelog language (default: English)
- `FORCE_UPDATE` - Override existing week entry (default: false)
- `DRY_RUN` - Preview without commit (default: false)
- `EXTENDED_ANALYSIS` - Detailed file statistics (default: false)
- `DAYS_BACK` - Lookback period in days (default: 7)

**Secrets location:**
- GitHub repository Settings > Secrets and variables > Actions > OPENROUTER_API_KEY

## Webhooks & Callbacks

**Incoming:**
- None - Action triggered by GitHub Actions events (schedule, workflow_dispatch, or manual trigger)

**Outgoing:**
- None - Changelog is committed directly to repository (via git-auto-commit-action@v5)

## Git Integration

**Git Operations:**
- Clone/fetch via `actions/checkout@v4` with dynamic depth (100/300/500 commits for 7/30/90+ days)
- Commit collection: `git log --since={date} --no-merges --pretty=format:'{fields}'`
- Extended stats: `git log --name-status --numstat` for file change analysis
- Commit: Automatic via stefanzweifel/git-auto-commit-action@v5 to branch `HEAD`

**Commit Metadata:**
- Full hash, subject, author, date extracted from git log
- Links generated to GitHub.com commit URLs: `https://github.com/{GITHUB_REPOSITORY}/commit/{full_hash}`

## Rate Limiting & Error Handling

**OpenRouter Rate Limiting:**
- Handled by exponential backoff retry logic (src/generate_changelog.py:23-33)
- 3 retry attempts with increasing delays for 429 errors
- Special handling: `delay * (3 ** attempt) + random.uniform(1, 5)` seconds
- Specific error detection for "429", "rate limit", "too many requests"

**API Error Handling:**
- 401 Unauthorized - Authentication failure with guidance to verify API key
- 404 Model Not Found - Model availability check with alternatives (gpt-5-mini, claude-3-haiku)
- Network timeout - Exponential backoff `delay * (2 ** attempt)`
- Generic errors - Max 3 attempts with 2-second base delay + jitter

**Fallback Behavior:**
- If API fails after retries, uses fallback text (configurable per language)
- Graceful degradation: Continues processing even if individual chunks fail (src/generate_changelog.py:568-571)

## Multi-Language Support

**Supported Languages:**
- English, Dutch, German, French, Spanish
- Language-specific configuration: src/generate_changelog.py:118-209
- Localizations:
  - Week/date labels
  - Section headers (Technical Changes, User Impact, etc.)
  - Fallback messages
  - Statistical terminology

---

*Integration audit: 2026-02-03*
