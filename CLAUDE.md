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
export MODEL="openai/gpt-4o-mini"
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
- **OPTIMIZED**: Dynamic fetch depth based on lookback period

### AI Integration
- **OPTIMIZED**: Enhanced retry logic with exponential backoff + jitter (3 attempts)
- **OPTIMIZED**: Specific handling for rate limiting (429 errors) with longer backoff
- **OPTIMIZED**: Comprehensive error handling with actionable guidance for auth, model, and network issues
- **Separate API calls**: Makes 2 independent calls (technical + business) for better formatting control
- **Token allocation**: 1200 tokens per summary (2400 total) for comprehensive, well-formatted output
- **Explicit markdown formatting**: Prompts include structured format examples with headers, bullets, and visual hierarchy
- Fallback summaries for API failures

### Performance Optimizations
- **OPTIMIZED**: Streaming support for large commit sets (>100 commits)
- **OPTIMIZED**: Memory-efficient chunked processing for very large repositories
- **OPTIMIZED**: Temporary file cleanup and cache management
- **OPTIMIZED**: Progress indicators for large operations

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

## Configuration

### Action Inputs
- `openrouter_api_key` (required): OpenRouter API key
- `github_token` (optional): Defaults to `${{ github.token }}`
- `days_back` (optional): 1-365 days, defaults to 7
- `model` (optional): OpenRouter model, defaults to 'openai/gpt-4o-mini'
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