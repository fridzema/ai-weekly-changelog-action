# Architecture Documentation

This document provides a comprehensive overview of the AI Weekly Changelog Action's architecture, including data flows, processing strategies, and key design decisions.

## Overview

The AI Weekly Changelog Action is a GitHub Action that automatically generates high-quality weekly changelogs from repository commits using AI models via OpenRouter. The system employs a **micro-chunking strategy** to ensure detailed analysis of large commit sets, splitting commits into small groups of 5 for focused AI analysis before merging into comprehensive summaries.

**Key Design Principles:**
- **Quality over cost**: Prioritizes summary quality through detailed micro-chunking (5 commits per chunk)
- **Comprehensive coverage**: Analyzes ALL commits, not just a subset
- **Graceful degradation**: Continues processing even if individual chunks fail
- **Multi-language support**: Generates changelogs in 5 languages with localized formatting

## High-Level Processing Flow

The action follows a sequential pipeline from input validation to changelog commit:

```mermaid
flowchart TD
    A[Start: GitHub Action Triggered] --> B[Input Validation]
    B --> C[Git Commit Collection]
    C --> D{Extended Analysis?}
    D -->|Yes| E[Collect File Statistics]
    D -->|No| F[Process Commits]
    E --> F
    F --> G{Commit Count > 5?}
    G -->|No| H[Single AI Analysis]
    G -->|Yes| I[Micro-Chunking Strategy]
    H --> J[Format Changelog]
    I --> J
    J --> K[Update CHANGELOG.md]
    K --> L[Commit Changes]
    L --> M[End: Changelog Updated]

    style G fill:#ffe6cc
    style I fill:#cce6ff
    style H fill:#cce6ff
```

## Micro-Chunking Strategy

The core innovation of this action is the micro-chunking approach that ensures comprehensive, high-quality analysis regardless of commit volume:

```mermaid
flowchart TD
    A[Commits Collection<br/>n commits] --> B{Count > 5?}
    B -->|No| C[Direct Analysis<br/>Single API Call]
    B -->|Yes| D[Split into Chunks<br/>~5 commits each]

    D --> E1[Chunk 1<br/>commits 1-5]
    D --> E2[Chunk 2<br/>commits 6-10]
    D --> E3[Chunk 3<br/>commits 11-15]
    D --> E4[...]
    D --> E5[Chunk n<br/>final commits]

    E1 --> F1[Technical Summary 1]
    E1 --> G1[Business Summary 1]
    E2 --> F2[Technical Summary 2]
    E2 --> G2[Business Summary 2]
    E3 --> F3[Technical Summary 3]
    E3 --> G3[Business Summary 3]
    E4 --> F4[...]
    E4 --> G4[...]
    E5 --> F5[Technical Summary n]
    E5 --> G5[Business Summary n]

    F1 & F2 & F3 & F4 & F5 --> H[Hierarchical Merge<br/>Technical Summaries]
    G1 & G2 & G3 & G4 & G5 --> I[Hierarchical Merge<br/>Business Summaries]

    C --> J[Final Technical<br/>& Business Summaries]
    H --> J
    I --> J
    J --> K[Formatted Changelog Entry]

    style B fill:#ffe6cc
    style D fill:#cce6ff
    style H fill:#e6ffe6
    style I fill:#e6ffe6
```

**Key Constants:**
- `COMMITS_PER_CHUNK = 5`: Maximum commits per chunk for focused analysis
- Each chunk receives **separate technical and business analysis**
- Chunk summaries are **merged hierarchically** to avoid API payload limits
- **2 API calls per chunk** (technical + business) + merge operations

**Example Scaling:**
- 30 commits = 6 chunks × 2 summaries = 12 chunk calls + 2 merge calls = **14 total API calls**
- 150 commits = 30 chunks × 2 summaries = 60 chunk calls + 2 merge calls = **62 total API calls**

## Data Flow Architecture

This diagram shows how data transforms through each stage of the pipeline:

```mermaid
flowchart LR
    A[Git Repository] -->|git log command| B[Raw Commit Data]
    B -->|Parse format:<br/>hash\|subject\|author\|date\|short_hash| C[Commit Objects]

    C --> D{Extended Mode?}
    D -->|Yes| E[File Statistics<br/>lines added/deleted<br/>files changed]
    D -->|No| F[Chunker Logic]
    E --> F

    F -->|Split into groups of 5| G[Commit Chunks]

    G --> H1[Chunk 1]
    G --> H2[Chunk 2]
    G --> H3[Chunk n]

    H1 --> I1[OpenRouter API<br/>Tech + Business]
    H2 --> I2[OpenRouter API<br/>Tech + Business]
    H3 --> I3[OpenRouter API<br/>Tech + Business]

    I1 -->|With retry logic| J1[Summary Pair 1]
    I2 -->|With retry logic| J2[Summary Pair 2]
    I3 -->|With retry logic| J3[Summary Pair n]

    J1 & J2 & J3 --> K[Hierarchical Merger]
    K --> L[Final Summaries<br/>Technical + Business]

    L --> M[Changelog Formatter]
    C --> M

    M -->|Week-based organization| N[CHANGELOG.md Entry]
    N --> O[Git Commit]

    style D fill:#ffe6cc
    style F fill:#cce6ff
    style K fill:#e6ffe6
```

## Extended Analysis Mode

When `extended: true` is enabled, the action collects additional file statistics for deeper analysis:

```mermaid
flowchart TD
    A[Extended Analysis Enabled] --> B[Collect File Changes]
    B --> C[Run git diff --numstat]
    C --> D[Parse Statistics]
    D --> E[Lines Added]
    D --> F[Lines Deleted]
    D --> G[Files Changed]

    E & F & G --> H[Group Files by Type]
    H --> I[*.py files<br/>*.md files<br/>*.yml files<br/>etc.]

    I --> J[Include in AI Prompts]
    J --> K{Prompt Size Check}
    K -->|Too Large| L[Truncate to 5000 chars]
    K -->|OK| M[Full Context]

    L --> N[AI Analysis with<br/>Extended Context]
    M --> N

    N --> O[Statistics Section<br/>in Changelog]
    O --> P[File Changes Summary]

    style K fill:#ffe6cc
    style L fill:#ffcccc
```

**Token Allocation for Extended Mode:**
- Standard mode: **3000 tokens** per summary
- Large commit sets (>100): **5000 tokens** per summary
- Extended analysis: **6000 tokens** per summary
- Merge operations: **6000 tokens** for combining summaries

**Safety Measures:**
- File changes data truncated to **5000 characters** max to prevent oversized prompts
- Prompt size validation before API calls (fail fast on >120K tokens)
- Graceful truncation with clear indicators in output

## Error Handling & Retry Strategy

The action implements comprehensive error handling with exponential backoff and specific handling for different error types:

```mermaid
flowchart TD
    A[API Call Attempt] --> B{Success?}
    B -->|Yes| C[Return Result]
    B -->|No| D[Check Error Type]

    D --> E{Error Type?}

    E -->|401/Unauthorized| F[Authentication Error]
    F --> G[Print API Key Help]
    G --> H[Exit: Auth Failed]

    E -->|404/Model Not Found| I[Model Availability Error]
    I --> J[Print Model Suggestions]
    J --> K[Exit: Model Error]

    E -->|429/Rate Limit| L[Rate Limiting Detected]
    L --> M{Retry Count < 3?}
    M -->|Yes| N[Wait: delay × 3^attempt<br/>+ jitter 1-5s]
    M -->|No| O[Exit: Rate Limit Exceeded]
    N --> A

    E -->|413/Payload Too Large| P[Payload Size Error]
    P --> Q[Hierarchical Merge Strategy]
    Q --> R[Reduce Batch Size]
    R --> A

    E -->|Timeout/Network| S[Network Error]
    S --> T{Retry Count < 3?}
    T -->|Yes| U[Wait: delay × 2^attempt<br/>+ jitter 0.5-2s]
    T -->|No| V[Exit: Network Failed]
    U --> A

    E -->|Other Error| W{Retry Count < 3?}
    W -->|Yes| X[Wait: delay × 2^attempt<br/>+ jitter 0.1-1s]
    W -->|No| Y[Fallback Summary]
    X --> A
    Y --> Z[Continue with Fallback]

    style E fill:#ffe6cc
    style M fill:#cce6ff
    style T fill:#cce6ff
    style W fill:#cce6ff
    style Q fill:#e6ffe6
```

**Retry Configuration:**
- **Max attempts**: 3 retries per API call
- **Base delay**: 2 seconds
- **Timeout**: 30 seconds per request
- **Exponential backoff**: `delay × 2^attempt` for standard errors
- **Rate limit backoff**: `delay × 3^attempt` for 429 errors (longer wait)
- **Jitter**: Random 0.1-5s added to prevent thundering herd

**Error-Specific Handling:**
- **401 (Auth)**: Immediate exit with API key setup instructions
- **404 (Model)**: Immediate exit with model availability guidance
- **429 (Rate Limit)**: Longer backoff (3× instead of 2×) with helpful messages
- **413 (Payload)**: Trigger hierarchical merge with smaller batches
- **Timeout/Network**: Standard retry with network troubleshooting tips
- **Other Errors**: Fallback to generic summary after max retries

## Hierarchical Merge Strategy

To handle very large commit sets and avoid 413 (Payload Too Large) errors, the system implements hierarchical merging:

```mermaid
flowchart TD
    A[30 Chunk Summaries] --> B{Count <= batch_size?}
    B -->|Yes| C[Direct Merge<br/>Single API Call]
    B -->|No| D[Split into Batches<br/>batch_size = 5]

    D --> E1[Batch 1: summaries 1-5]
    D --> E2[Batch 2: summaries 6-10]
    D --> E3[Batch 3: summaries 11-15]
    D --> E4[Batch 4: summaries 16-20]
    D --> E5[Batch 5: summaries 21-25]
    D --> E6[Batch 6: summaries 26-30]

    E1 --> F1[Merge Batch 1<br/>API Call]
    E2 --> F2[Merge Batch 2<br/>API Call]
    E3 --> F3[Merge Batch 3<br/>API Call]
    E4 --> F4[Merge Batch 4<br/>API Call]
    E5 --> F5[Merge Batch 5<br/>API Call]
    E6 --> F6[Merge Batch 6<br/>API Call]

    F1 & F2 & F3 & F4 & F5 & F6 --> G[6 Merged Summaries]

    G --> H{Count <= batch_size?}
    H -->|Yes| I[Final Merge<br/>API Call]
    H -->|No| J[Recursive Batching]
    J --> I

    I --> K[Single Final Summary]
    C --> K

    style B fill:#ffe6cc
    style D fill:#cce6ff
    style H fill:#ffe6cc
    style J fill:#ffcccc
```

**Adaptive Batching:**
- Default batch size: **5 summaries per merge**
- If merge fails with 413 error: **Reduce batch size by 1** and retry
- Recursive merging continues until single summary produced
- Safety limit: Minimum batch size of **2** to ensure progress

## Multi-Language Support

The action supports 5 languages with complete localization:

```mermaid
flowchart LR
    A[Language Input] --> B{Supported?}
    B -->|Yes| C[Load Language Config]
    B -->|No| D[Warning Message]
    D --> E[Fallback to English]
    E --> C

    C --> F[Language Configuration]
    F --> G[Date Formats]
    F --> H[Section Headers]
    F --> I[Labels & Terms]
    F --> J[Fallback Messages]

    G --> K[Applied to Changelog]
    H --> K
    I --> K
    J --> K

    K --> L[Localized Changelog Entry]

    style B fill:#ffe6cc
    style D fill:#ffcccc
```

**Supported Languages:**
- **English**: Default, `MM-DD-YYYY` date format
- **Dutch**: `DD-MM-YYYY` format
- **German**: `DD.MM.YYYY` format
- **French**: `DD/MM/YYYY` format
- **Spanish**: `DD/MM/YYYY` format

**Localized Elements:**
- Week labels, date formats, commit counts
- Section headers (Technical Changes, User Impact, Statistics, etc.)
- Statistical terminology (lines added/deleted, files changed)
- Fallback messages when AI generation fails
- Force update indicators

## Performance Characteristics

**Processing Time:**
- Small sets (≤5 commits): ~5-10 seconds (single analysis)
- Medium sets (30 commits): ~30-60 seconds (6 chunks + merges)
- Large sets (150 commits): ~2-4 minutes (30 chunks + hierarchical merges)

**API Call Volume:**
- Direct formula: `(commits / 5) × 2 + merge_calls`
- Small sets: **2 calls** (technical + business)
- 30 commits: **~14 calls** (12 chunk + 2 merge)
- 150 commits: **~62 calls** (60 chunk + 2 merge)

**Memory Efficiency:**
- Commits processed in batches of 50 for parsing
- Progress indicators for sets >200 commits
- Temporary file cleanup after processing
- Extended data truncation to prevent memory bloat

## Security & API Key Management

**API Key Redaction:**
- Exact match redaction of full API key from all error messages
- Regex pattern matching for `sk-or-*` format
- Shows first 4 characters for debugging (e.g., `sk-or-...[REDACTED]`)
- Applied to all exception handling and logging

**Validation:**
- Checks for `OPENROUTER_API_KEY` environment variable
- Validates format (should start with `sk-or-`)
- Provides setup instructions if missing or invalid
- Never logs full API key to console or files

## Changelog Management

**Week-Based Organization:**
- Uses ISO week numbers for consistent grouping
- Format: `Week {number}, {year}`
- Entries sorted newest first
- Automatic duplicate detection

**Force Update Mode:**
- `force: true` allows overwriting existing week entries
- Removes old entry before inserting new one
- Adds `(Force Updated)` indicator to header
- Preserves other changelog sections

**Structure:**
```
# Changelog

This file is automatically updated with weekly changes.

## Week 6, 2026 (Force Updated)

*Generated on 02-06-2026 - 30 commits*

> 📊 **Note**: This changelog was generated by analyzing 30 commits across 6 detailed chunks...

### 🔧 Technical Changes
[AI-generated technical summary with markdown formatting]

### 📈 User Impact
[AI-generated business summary with markdown formatting]

### 📊 Statistics (Extended mode only)
- **150** lines added
- **42** lines deleted
- **12** files changed

### 📋 All Commits
- [abc123] Fix authentication bug - John Doe
- [def456] Add user dashboard - Jane Smith
...

---
```

## Related Documentation

- **[../README.md](../README.md)**: Usage instructions and examples
- **[../CLAUDE.md](../CLAUDE.md)**: Development guide and troubleshooting
- **[../src/generate_changelog.py](../src/generate_changelog.py)**: Implementation source code
