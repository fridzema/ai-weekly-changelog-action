---
phase: quick-001
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - src/generate_changelog.py
autonomous: true

must_haves:
  truths:
    - "Technical and business chunk summaries for the same chunk run in parallel, cutting per-chunk API time roughly in half"
    - "Multiple chunks run concurrently with configurable concurrency limit to respect rate limits"
    - "If a run fails partway through, previously generated chunk summaries are reused on the next run"
    - "All existing behavior (fallbacks, retry logic, hierarchical merge, extended analysis) continues to work unchanged"
  artifacts:
    - path: "src/generate_changelog.py"
      provides: "Parallel API calls via ThreadPoolExecutor and chunk-level response caching"
      contains: "ThreadPoolExecutor"
  key_links:
    - from: "generate_chunked_summary"
      to: "concurrent.futures.ThreadPoolExecutor"
      via: "parallel chunk execution with rate-limit-aware concurrency"
      pattern: "ThreadPoolExecutor"
    - from: "generate_chunked_summary"
      to: "/tmp/changelog_cache/"
      via: "chunk-level cache keyed on commit content hash"
      pattern: "chunk_cache"
---

<objective>
Parallelize API calls in generate_changelog.py and add chunk-level response caching for resilience.

Purpose: The current sequential processing means 30 commits (6 chunks x 2 summary types = 12 API calls) run one-by-one. Parallelizing tech+business per chunk and running multiple chunks concurrently can cut total API wait time by 50-70%. Chunk-level caching means partial failures don't waste completed work.

Output: Updated `src/generate_changelog.py` with parallel execution and chunk caching.
</objective>

<context>
@src/generate_changelog.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Parallelize API calls with ThreadPoolExecutor</name>
  <files>src/generate_changelog.py</files>
  <action>
Refactor `generate_chunked_summary` and its callers in `src/generate_changelog.py` to use `concurrent.futures.ThreadPoolExecutor` for parallel API calls. The script currently makes two top-level sequential calls (lines 886-906): one `generate_chunked_summary` for tech, one for business. Within each, chunks are also sequential (lines 848-883).

Specific changes:

1. Add `import concurrent.futures` and `import hashlib` at the top of the file (these are stdlib, no new deps).

2. Add a `MAX_CONCURRENT_CHUNKS` constant near `COMMITS_PER_CHUNK` (line 634). Default to `3`. This limits how many chunks are processed in parallel to avoid rate limiting. Add a comment explaining the trade-off: higher = faster but more likely to hit 429s.

3. Refactor the TWO top-level `generate_chunked_summary` calls (tech on line 887, business on line 898) to run in parallel using `ThreadPoolExecutor(max_workers=2)`. Use `executor.submit()` for each, then collect results with `.result()`. Wrap each `.result()` call in its own try/except to preserve the existing per-summary fallback behavior (lines 891-895 for tech, 902-906 for business). This alone cuts total time nearly in half since tech and business summaries are completely independent.

4. Inside `generate_chunked_summary`, refactor the sequential chunk loop (lines 850-873) to use `ThreadPoolExecutor(max_workers=MAX_CONCURRENT_CHUNKS)`. Submit all chunks as futures, then collect results maintaining order via `enumerate`. Each future calls `generate_summary` for its chunk. On failure, append the existing fallback message (line 871-873) for that chunk. Use `as_completed` for progress logging but store results in an ordered dict/list to maintain chunk order for merging.

5. Keep the `@retry_api_call` decorator on `generate_summary` and `merge_chunk_summaries` unchanged - retries happen per-call inside each thread, which is correct.

6. Thread safety note: The `client` (OpenAI) object is thread-safe for concurrent `.chat.completions.create()` calls. The `print()` calls may interleave but that is acceptable for log output.

Do NOT change the merge logic (`hierarchical_merge_summaries`, `merge_chunk_summaries`). Merging still happens sequentially after all chunks complete, which is correct.

Do NOT add any new dependencies to requirements.txt. `concurrent.futures` and `hashlib` are stdlib.
  </action>
  <verify>
Run `python3 -c "import ast; ast.parse(open('src/generate_changelog.py').read()); print('Syntax OK')"` to verify no syntax errors. Then run `python3 -c "from concurrent.futures import ThreadPoolExecutor; print('Import OK')"` to confirm stdlib availability. Grep for `ThreadPoolExecutor` in the file to confirm it was added.
  </verify>
  <done>
The script uses ThreadPoolExecutor to: (1) run tech and business generate_chunked_summary in parallel at the top level, and (2) run multiple chunks concurrently within each generate_chunked_summary call, limited by MAX_CONCURRENT_CHUNKS=3. All existing error handling, retry logic, and fallback behavior is preserved.
  </done>
</task>

<task type="auto">
  <name>Task 2: Add chunk-level AI response caching</name>
  <files>src/generate_changelog.py</files>
  <action>
Add a chunk-level caching layer so that individual chunk AI responses are cached and reused if the script is re-run (e.g., after a partial failure or timeout). This complements the existing git-level caching in action.yml.

Specific changes:

1. Create a helper function `get_chunk_cache_key(chunk_commits_text: str, summary_type: str, model: str) -> str` that returns a deterministic cache key. Use `hashlib.sha256(f"{chunk_commits_text}|{summary_type}|{model}|{output_language}".encode()).hexdigest()[:16]`. This means the same commits with the same model and language always produce the same cache key, regardless of HEAD or run timing.

2. Create a helper function `get_chunk_cache_dir() -> str` that returns `/tmp/changelog_cache/chunks/` and ensures the directory exists via `os.makedirs(..., exist_ok=True)`.

3. Create `read_chunk_cache(cache_key: str) -> str | None` that reads from `{cache_dir}/{cache_key}.txt` and returns the content, or None if the file doesn't exist or is empty.

4. Create `write_chunk_cache(cache_key: str, content: str) -> None` that writes content to `{cache_dir}/{cache_key}.txt`.

5. In `generate_chunked_summary`, before calling `generate_summary` for a chunk, compute the cache key from the chunk's commits text + summary_type. Check cache first. If cache hit, print `"   Cache hit for chunk {N} {description}"` and use the cached result. If cache miss, call `generate_summary` as before, then write the result to cache.

6. Add a `cleanup_chunk_cache(max_age_hours: int = 48) -> None` function that removes chunk cache files older than max_age_hours. Call this once at the beginning of the main block (near line 349), before processing starts. Use `os.path.getmtime()` and `time.time()` for age calculation.

7. Print a summary line after chunk processing: `"   Cache: {hits} hits, {misses} misses out of {total} chunks"`.

Important: The cache is keyed on commit CONTENT (not HEAD hash), so if the same commits appear in a re-run, they hit cache even if other commits were added. This makes partial-failure recovery work correctly.

Do NOT modify action.yml or requirements.txt.
  </action>
  <verify>
Run `python3 -c "import ast; ast.parse(open('src/generate_changelog.py').read()); print('Syntax OK')"` to verify no syntax errors. Grep for `chunk_cache` and `sha256` in the file to confirm caching was added. Verify the cache directory path is `/tmp/changelog_cache/chunks/`.
  </verify>
  <done>
Chunk-level caching is implemented: each chunk's AI response is cached to disk keyed on commit content + model + language. Re-runs reuse cached chunks. A cleanup function removes stale cache files older than 48 hours. Cache hit/miss stats are logged.
  </done>
</task>

</tasks>

<verification>
1. `python3 -c "import ast; ast.parse(open('src/generate_changelog.py').read()); print('Syntax OK')"` - file parses without errors
2. `grep -c "ThreadPoolExecutor" src/generate_changelog.py` - returns at least 2 (top-level parallel + chunk-level parallel)
3. `grep -c "chunk_cache" src/generate_changelog.py` - returns multiple matches confirming cache integration
4. `grep "MAX_CONCURRENT_CHUNKS" src/generate_changelog.py` - constant exists with default of 3
5. `grep "sha256" src/generate_changelog.py` - content-based cache key generation exists
6. `grep "concurrent.futures" src/generate_changelog.py` - import exists
7. Manual review: existing `@retry_api_call` decorators unchanged, `hierarchical_merge_summaries` unchanged, fallback behavior preserved
</verification>

<success_criteria>
- ThreadPoolExecutor parallelizes tech+business summary generation at the top level
- ThreadPoolExecutor parallelizes chunk processing within each summary type (max 3 concurrent)
- Chunk-level cache stores individual AI responses keyed on commit content hash
- Cache hits skip API calls, cache misses write results for future runs
- Stale cache cleanup runs at startup (48h TTL)
- No new dependencies added (concurrent.futures and hashlib are stdlib)
- All existing error handling, retry logic, and fallback summaries work unchanged
- Merge logic (hierarchical_merge_summaries) remains sequential and unchanged
</success_criteria>

<output>
After completion, create `.planning/quick/001-performance-optimizations-caching-improv/001-SUMMARY.md`
</output>
