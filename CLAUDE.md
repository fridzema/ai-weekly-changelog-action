# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a GitHub Action that automatically generates weekly changelogs from repository commits using AI models via OpenRouter. The action analyzes git commit history, generates technical and business summaries using AI, and commits the results to a `CHANGELOG.md` file.

## Architecture

### Core Components

- **action.yml**: GitHub Action definition with composite steps for validation, commit collection, Python setup, and changelog generation
- **src/generate_changelog.py**: Main Python script that handles AI-powered changelog generation with multi-language support
- **requirements.txt**: Python dependencies (openai>=1.14,<2, requests)

### Key Workflows

1. **Input Validation**: Validates `days_back` parameter (1-365 range)
2. **Commit Collection**: Uses optimized git operations to collect recent commits with filtering for merge commits and version updates  
3. **Extended Analysis** (optional): Collects detailed file change statistics and numstat data
4. **AI Generation**: Uses OpenRouter API with retry logic and fallback summaries
5. **Changelog Update**: Formats and commits changelog with week-based organization

### Multi-Language Support

The system supports English, Dutch, German, French, and Spanish with localized:
- Date formats
- Section headers and labels  
- Fallback messages
- Statistical terminology

## Development Commands

### Testing the Action Locally

Since this is a GitHub Action, local testing requires simulating the GitHub environment:

```bash
# Set required environment variables
export OPENROUTER_API_KEY="your-key-here"
export GITHUB_REPOSITORY="owner/repo-name"
export MODEL="openai/gpt-5-mini"
export OUTPUT_LANGUAGE="English"

# Create test commit data
git log --since="7 days ago" --no-merges --pretty=format:'%H|%s|%an|%ad|%h' --date=short > commits.txt

# Run the Python script directly
python3 src/generate_changelog.py
```

### Dependencies

Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Technical Details

### Git Filtering Strategy
- Excludes merge commits (`--no-merges`)
- Filters out version update commits and documentation updates
- **OPTIMIZED**: Consolidated git operations using single command with multiple formats
- **OPTIMIZED**: Intelligent caching system based on repository state and parameters
- **OPTIMIZED**: Dynamic fetch depth based on lookback period (100/300/500 commits for 7/30/90+ days)
- **ENHANCED**: Increased fetch depths to handle active repositories (previously 50/100/200)

### AI Integration
- **OPTIMIZED**: Enhanced retry logic with exponential backoff + jitter (3 attempts)
- **OPTIMIZED**: Specific handling for rate limiting (429 errors) with longer backoff
- **OPTIMIZED**: Comprehensive error handling with actionable guidance for auth, model, and network issues
- **INTELLIGENT CHUNKING**: Automatically splits large commit sets (>5 commits) into small, focused chunks for highly detailed analysis
  - **Micro-chunking approach**: Maximum 5 commits per chunk for focused, detailed analysis
  - Each chunk is analyzed separately with full context and attention to detail
  - Chunk summaries are merged using AI to create cohesive, comprehensive final output
  - Visual indicators in changelog when chunking is used
  - **Quality over quantity**: More API calls but significantly better summary quality
- **Separate API calls**: Makes 2 independent calls per chunk (technical + business) for better formatting control
- **Token allocation**: 3000-6000 tokens per summary (dynamic scaling based on commit count and analysis mode)
  - Standard mode: 3000 tokens per summary
  - Large commit sets (>100): 5000 tokens per summary
  - Extended analysis: 6000 tokens per summary
  - Merge operations: 6000 tokens for combining chunk summaries
- **Explicit markdown formatting**: Prompts include structured format examples with headers, bullets, and visual hierarchy
- Fallback summaries for API failures

### Dependency Management
- Minimal dependencies: `openai>=1.14,<2` and `requests`
- Fast installation: ~5-10 seconds (no caching needed for 2 packages)
- Note: Pip caching not used in composite actions due to path resolution issues

### Performance Optimizations
- **MICRO-CHUNKING STRATEGY**: Automatic chunking for commit sets >5 commits
  - **Small chunks of ~5 commits each** for highly detailed, focused AI analysis
  - Each commit receives focused attention in its chunk context
  - Sequential processing with comprehensive retry logic per chunk
  - Progress indicators showing chunk completion (e.g., "✅ Chunk 12/30 technical summary completed")
  - **Trade-off**: More API calls for significantly better summary quality and completeness
- **OPTIMIZED**: Memory-efficient processing for very large repositories (200+ commits)
- **OPTIMIZED**: Temporary file cleanup and cache management
- **OPTIMIZED**: Commit count validation with warnings for potentially incomplete data
- **ENHANCED**: Graceful degradation - continues processing even if individual chunks fail
- **Cost-aware**: Typical processing:
  - 30 commits = 6 chunks × 2 summaries = 12 chunk API calls + 2 merge calls = ~14 API calls
  - 150 commits = 30 chunks × 2 summaries = 60 chunk API calls + 2 merge calls = ~62 API calls

### Caching System
- Cache key based on: `{latest_commit_hash}_{days_back}_{extended_mode}`
- Stored in `/tmp/changelog_cache/` with automatic cleanup
- Separate caching for basic and extended analysis results
- Cache hit detection skips expensive git operations

### Error Handling & User Guidance
- Detailed error messages with specific resolution steps
- API key validation and format checking
- Rate limiting detection with suggested wait times
- Model availability checks with alternative suggestions
- Network issue detection and retry strategies

### Changelog Management
- Week-based organization using ISO week numbers
- Force update capability to overwrite existing entries
- Automatic duplicate detection and prevention
- Maintains changelog structure with proper markdown formatting

## Troubleshooting Large Commit Sets

### Symptoms of Incomplete Changelog
- Summary appears cut off or incomplete
- Only seeing a few commits despite long time period (e.g., 30 days)
- Mismatch between summary content and "All Commits" list
- Missing recent features or changes in the technical/business summaries

### Root Causes
1. **Insufficient Git Fetch Depth** (Fixed in current version)
   - Previously: 50/100/200 commits for 7/30/90+ days
   - Now: 100/300/500 commits for 7/30/90+ days
   - If you still see issues, the repository may be extremely active

2. **Old Chunking Logic** (Fixed in current version)
   - Previously: Hard limit of 100 commits, rest ignored
   - Now: Micro-chunking analyzes ALL commits in small groups of 5 for detailed, focused analysis

### Verification Steps
1. **Check GitHub Actions logs** for these indicators:
   ```
   📊 Large commit set detected (X commits)
   🔄 Will analyze in Y chunks of ~5 commits each for detailed analysis
   💡 This approach ensures each commit gets focused attention before merging into comprehensive summary
   ✅ Chunk 1/Y technical summary completed
   ✅ Chunk 1/Y business summary completed
   ...
   🔄 Merging Y technical chunk summaries...
   🔄 Merging Y business chunk summaries...
   ```
   Note: With 30 commits, expect ~6 chunks; with 150 commits, expect ~30 chunks

2. **Check CHANGELOG.md** for chunking indicator:
   ```markdown
   > 📊 **Note**: This changelog was generated by analyzing X commits across Y detailed chunks for comprehensive, high-quality coverage.
   ```

3. **Validate commit count** matches expectations:
   - Look at GitHub Actions step summary: "Commits processed: X"
   - Compare with `git log --since="30 days ago" --oneline | wc -l`

### For Extremely Active Repositories (>500 commits/month)
If you're still experiencing issues with very high commit volumes:

1. **Increase fetch depth** in your workflow:
   ```yaml
   - name: Checkout repository
     uses: actions/checkout@v4
     with:
       fetch-depth: 1000  # Increase if needed
   ```

2. **Reduce lookback period**:
   - Use `days_back: 14` instead of `days_back: 30`
   - Run changelog more frequently (weekly instead of monthly)

3. **Monitor API costs**:
   - **Micro-chunking = many more API calls** for better quality
   - Typical costs with GPT-5-mini (estimated):
     - 30 commits: ~14 API calls ≈ $0.05-0.15 per changelog
     - 150 commits: ~62 API calls ≈ $0.20-0.80 per changelog
     - 300 commits: ~122 API calls ≈ $0.40-1.50 per changelog
   - **Quality vs Cost trade-off**: Micro-chunking prioritizes summary quality over API costs
   - Consider using smaller `days_back` values for cost optimization
   - Alternatively, increase `COMMITS_PER_CHUNK` in the code (line 380) if cost is a concern

## Configuration

### Action Inputs
- `openrouter_api_key` (required): OpenRouter API key
- `github_token` (optional): Defaults to `${{ github.token }}`
- `days_back` (optional): 1-365 days, defaults to 7
- `model` (optional): OpenRouter model, defaults to 'openai/gpt-5-mini'
- `language` (optional): Output language, defaults to 'English'
- `force` (optional): Force update existing entries
- `extended` (optional): Enable detailed file analysis

### Output Structure
Generated changelog includes:
- Week header with generation metadata
- Technical changes summary for developers
- User impact summary for stakeholders  
- Statistics section (when extended analysis enabled)
- Complete commit list with GitHub links