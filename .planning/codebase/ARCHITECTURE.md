# Architecture

**Analysis Date:** 2026-02-03

## Pattern Overview

**Overall:** GitHub Actions Composite Action with AI-powered backend

**Key Characteristics:**
- Decoupled workflow orchestration (YAML-based steps) and Python implementation
- Stateless processing pipeline with caching layer
- Intelligent chunking strategy for handling variable commit volumes
- Retry-driven error resilience with exponential backoff and rate-limit awareness

## Layers

**GitHub Actions Orchestration (Workflow Layer):**
- Purpose: Coordinate input validation, git operations, Python execution, and output handling
- Location: `action.yml`
- Contains: 7 composite steps (validation, checkout, commit collection, Python setup, changelog generation, git commit, summary output)
- Depends on: GitHub Actions runtime context, git CLI, Python environment
- Used by: GitHub Actions scheduler and manual workflow triggers

**Commit Collection & Caching Layer:**
- Purpose: Extract commit data with intelligent filtering, caching, and extended analysis support
- Location: `action.yml` (lines 61-208, "Collect commits and file changes" step)
- Contains: Git log operations, cache key generation, parallel data collection for extended mode
- Depends on: Git repository, filesystem (/tmp/changelog_cache)
- Used by: Python changelog generation script

**AI Generation Layer:**
- Purpose: Transform commit data into human-readable technical and business summaries
- Location: `src/generate_changelog.py`
- Contains: OpenRouter API integration, retry decorator, chunked processing, merge operations
- Depends on: OpenRouter API, OpenAI Python client, language configuration maps
- Used by: Changelog formatting and output step

**Changelog Management Layer:**
- Purpose: Maintain CHANGELOG.md file with week-based entries, duplicate detection, and force update logic
- Location: `src/generate_changelog.py` (lines 612-722)
- Contains: File I/O, duplicate detection, section insertion logic, language-specific formatting
- Depends on: Filesystem, existing CHANGELOG.md structure
- Used by: Git auto-commit action

## Data Flow

**Standard Execution Flow:**

1. **Input Validation** (action.yml, lines 46-54)
   - Validates `days_back` parameter is 1-365 integer
   - Exits if invalid

2. **Checkout & Dynamic Fetch** (action.yml, lines 56-59)
   - Checks out repository with dynamic fetch-depth
   - Fetch-depth scales: 100 (7 days), 300 (30 days), 500 (90+ days)

3. **Commit Collection** (action.yml, lines 61-208)
   - Check cache key: `{latest_commit_hash}_{days_back}_{extended_mode}`
   - If cache hit: Load commits.txt, commits_extended.txt, files_changed.txt from `/tmp/changelog_cache`
   - If cache miss: Execute parallel git operations:
     - `git log --since --no-merges --pretty=format` → commits.txt
     - `git log --since --no-merges --name-status` → commits_extended.txt (extended mode)
     - `git log --since --no-merges --numstat` → aggregate statistics (extended mode)
   - Cache results with metadata file
   - Cleanup old cache files (keep last 5 sets)
   - Output: `has_commits`, `commit_count`, extended analysis flags

4. **Python Setup & Execution** (action.yml, lines 210-238)
   - Setup Python 3.11
   - Install dependencies: openai>=1.14,<2, requests
   - Execute: `python3 ${{ github.action_path }}/src/generate_changelog.py`
   - Pass environment: OPENROUTER_API_KEY, MODEL, OUTPUT_LANGUAGE, FORCE_UPDATE, DRY_RUN, extended flags

5. **Changelog Generation** (src/generate_changelog.py)
   - Parse commits.txt, extended data, file changes
   - Detect chunking requirement (total_commits > 5)
   - If chunking: Process in chunks of 5 commits each with separate technical/business summaries per chunk
   - Merge chunk summaries into unified output via API
   - Generate CHANGELOG.md entry with week-based header
   - Handle force update: Remove existing week entry if present

6. **Commit & Output** (action.yml, lines 248-291)
   - If dry_run=false: Use `stefanzweifel/git-auto-commit-action@v5` to commit CHANGELOG.md
   - Output step summary with generation metadata
   - If dry_run=true: Display changelog preview (first 100 lines) to step summary

**State Management:**
- **Stateless between executions**: Each run independently collects commits and generates changelog
- **Cache state**: Temporary cache in /tmp with automatic cleanup (keeps 5 recent sets)
- **Changelog state**: Persistent CHANGELOG.md file (deduplicated by week header)
- **Error state**: Graceful degradation with fallback summaries

## Key Abstractions

**@retry_api_call Decorator:**
- Purpose: Implement resilient API calls with smart error handling
- Location: `src/generate_changelog.py` (lines 10-79)
- Pattern: Function wrapper with exponential backoff (2^attempt + jitter)
- Special handling:
  - 429 Rate Limit: 3^attempt delay + 1-5s jitter, longer waits
  - 401 Authentication: Fails immediately with helpful guidance
  - 404 Model Not Found: Fails immediately with model suggestions
  - Network errors: 2^attempt delay + 0.5-2s jitter, retries
  - Generic errors: 2^attempt delay + 0.1-1s jitter

**Language Configuration Maps:**
- Purpose: Centralize multi-language terminology and fallbacks
- Location: `src/generate_changelog.py` (lines 118-209)
- Languages: English, Dutch, German, French, Spanish
- Keys: week_label, generated_on, commits_label, tech_changes, user_impact, all_commits, statistics, file_changes, changelog_title, auto_updated, fallback_tech, fallback_business, lines_added, lines_deleted, files_changed, force_updated

**Chunked Summary Generation:**
- Purpose: Provide detailed analysis of large commit sets by processing small focused groups
- Location: `src/generate_changelog.py` (lines 543-579)
- Pattern:
  - No chunking: commits <= 5 (single API call per summary type)
  - With chunking: commits > 5 (5 commits per chunk, separate technical/business per chunk)
  - Chunk processing: Sequential with 3 retry attempts per chunk
  - Merge operation: Separate API call to consolidate chunk results

**Intelligent Token Allocation:**
- Purpose: Scale API response quality based on content scope
- Location: `src/generate_changelog.py` (lines 510-515)
- Rules:
  - Standard: 3000 tokens per summary
  - Large sets (>100 commits): 5000 tokens
  - Extended analysis: 6000 tokens
  - Merge operations: 6000 tokens

## Entry Points

**Workflow Scheduler:**
- Location: Defined in consuming repository's `.github/workflows/*.yml`
- Triggers: Scheduled cron (e.g., "0 6 * * MON") or manual workflow_dispatch
- Responsibilities: Invoke action with specified inputs

**Action Execution:**
- Location: `action.yml` root composite definition
- Triggers: GitHub Actions event
- Responsibilities: Orchestrate 7 sequential steps

**Python Script Entrypoint:**
- Location: `src/generate_changelog.py` (module-level, lines 81-723)
- Triggers: Invoked by action step "Generate changelog with OpenRouter"
- Responsibilities:
  - Validate API key presence and format
  - Initialize OpenRouter client
  - Parse commits and extended data from disk
  - Determine chunking strategy
  - Generate technical and business summaries
  - Manage CHANGELOG.md file (create, update, deduplicate)
  - Output status messages

## Error Handling

**Strategy:** Defensive with fallback mechanisms and actionable error messages

**Patterns:**

**Input Validation Failures (action.yml):**
- Validate days_back is 1-365 integer
- Exit with code 1 if invalid
- Print specific error and guidance

**Git Operations Failures:**
- Simple mode fallback: If advanced git filters fail, retry with basic --no-merges
- Commit count validation: Warn if unusually low commit count for period
- Cache miss detection: Skip cache if files incomplete, re-run git ops

**API Call Failures (src/generate_changelog.py):**
- Rate limiting (429): Retry with 3^attempt backoff, suggest waiting, fail after 3 attempts
- Authentication (401): Fail immediately with key validation URL and guidance
- Model not found (404): Fail immediately with model suggestions
- Network errors: Retry with 2^attempt backoff, fail after 3 attempts
- Generic errors: Retry with 2^attempt backoff, fail after 3 attempts

**Chunk Processing Failures:**
- Single chunk failure: Log warning, append "[Chunk X failed - not included]" placeholder
- Continue with other chunks (graceful degradation)
- Merge operation: Use chunk that succeeded, skip chunk that failed

**Changelog Writing Failures:**
- File permission issues: Print error and common causes
- Disk space issues: Print error and common causes
- Invalid markdown: Print error and common causes
- Exit with code 1, cleanup temp files

**Fallback Mechanisms:**
- API failure on tech summary: Use config['fallback_tech'] (1-2 sentence generic)
- API failure on business summary: Use config['fallback_business'] (1-2 sentence generic)
- No commits found: Skip Python execution, output "No Changes This Week"

## Cross-Cutting Concerns

**Logging:**
- Approach: Print-based (stdout captured by GitHub Actions)
- Emoji prefixes: 🤖 (model), 🌍 (language), ✅ (success), ❌ (error), ⚠️ (warning), 🔄 (processing), 📊 (data)
- Levels: Info (no prefix), Success (✅), Warning (⚠️), Error (❌)

**Validation:**
- Approach: Early validation at action.yml level (inputs) and Python module level (environment)
- API key format check: Expect OpenRouter format starting with "sk-or-"
- Environment variable parsing: Type conversion for boolean flags, fallback defaults

**Authentication:**
- Approach: OpenRouter API key via OPENROUTER_API_KEY environment variable
- Initialization: In Python, validated at module load time (lines 82-96)
- Transmission: Passed to OpenAI client constructor as base URL + API key

**Caching:**
- Approach: File-based cache in /tmp/changelog_cache with metadata files
- Key generation: Hash of (HEAD commit, days_back, extended_mode)
- Hit detection: Check existence and completeness of cache files
- Cleanup: Automatic removal of files older than 5 most recent cache sets
