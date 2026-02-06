from __future__ import annotations

import concurrent.futures
import datetime
import hashlib
import os
import re
import sys
import tempfile
import textwrap
import time
from functools import wraps
from typing import Any, Callable, TypeVar

from openai import OpenAI

T = TypeVar("T")


def redact_api_key(text: str) -> str:
    """Redact API key from error messages to prevent accidental exposure."""
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if api_key and len(api_key) > 8:
        # Redact the full key, showing only first 4 chars for debugging
        redacted = api_key[:4] + "..." + "[REDACTED]"
        text = text.replace(api_key, redacted)
    # Also catch common API key patterns that might appear

    # Redact any sk-or-* pattern (OpenRouter keys)
    text = re.sub(r"sk-or-[a-zA-Z0-9_-]+", "sk-or-...[REDACTED]", text)
    return text


def process_commits_in_chunks(
    commits_raw: str, repo_url: str | None = None, chunk_size: int = 50
) -> tuple[list[str], list[str]]:
    """Process commits in chunks to handle large commit sets efficiently.

    Args:
        commits_raw: Raw commit string with format: hash|subject|author|date|short_hash
        repo_url: GitHub repository URL for commit links
        chunk_size: Number of commits to process per chunk

    Returns:
        Tuple of (commits_formatted, commit_links)
    """
    if repo_url is None:
        repo_url = f"https://github.com/{os.getenv('GITHUB_REPOSITORY', 'unknown')}"

    lines = commits_raw.strip().split("\n") if commits_raw.strip() else []
    local_commits_formatted = []
    local_commit_links = []

    # Process in smaller chunks to manage memory for very large sets
    for i in range(0, len(lines), chunk_size):
        chunk = lines[i : i + chunk_size]

        for line in chunk:
            if "|" in line:
                parts = line.split("|")
                if len(parts) >= 5:
                    full_hash, subject, author, date, short_hash = parts[:5]
                    local_commits_formatted.append(f"• {subject} ({author}, {date})")
                    local_commit_links.append(
                        f"- [{short_hash}]({repo_url}/commit/{full_hash}) {subject} - {author}"
                    )
                else:
                    local_commits_formatted.append(f"• {line}")
                    local_commit_links.append(f"- {line}")
            else:
                local_commits_formatted.append(f"• {line}")
                local_commit_links.append(f"- {line}")

        # Progress indicator for very large sets
        if len(lines) > 200 and i % (chunk_size * 4) == 0:
            print(
                f"📊 Processed {min(i + chunk_size, len(lines))}/{len(lines)} commits..."
            )

    return local_commits_formatted, local_commit_links


def get_language_config(language: str) -> dict[str, str]:
    """Get language configuration for changelog generation.

    Args:
        language: Language name (English, Dutch, German, French, Spanish)

    Returns:
        Dict with language-specific labels and text
    """
    language_configs = {
        "English": {
            "week_label": "Week",
            "generated_on": "Generated on",
            "commits_label": "commits",
            "tech_changes": "🔧 Technical Changes",
            "user_impact": "📈 User Impact",
            "all_commits": "📋 All Commits",
            "statistics": "📊 Statistics",
            "file_changes": "📁 File Changes",
            "changelog_title": "Changelog",
            "auto_updated": "This file is automatically updated with weekly changes.",
            "fallback_tech": "Technical changes were made this week. See commit details below for specifics.",
            "fallback_business": "Various improvements and updates were implemented this week.",
            "lines_added": "lines added",
            "lines_deleted": "lines deleted",
            "files_changed": "files changed",
            "force_updated": "(Force Updated)",
        },
        "Dutch": {
            "week_label": "Week",
            "generated_on": "Gegenereerd op",
            "commits_label": "commits",
            "tech_changes": "🔧 Technische wijzigingen",
            "user_impact": "📈 Impact voor gebruikers",
            "all_commits": "📋 Alle commits",
            "statistics": "📊 Statistieken",
            "file_changes": "📁 Bestandswijzigingen",
            "changelog_title": "Changelog",
            "auto_updated": "Dit bestand wordt automatisch bijgewerkt met wekelijkse wijzigingen.",
            "fallback_tech": "Er zijn deze week technische wijzigingen doorgevoerd. Zie onderstaande commit details.",
            "fallback_business": "Deze week zijn diverse verbeteringen en updates doorgevoerd.",
            "lines_added": "regels toegevoegd",
            "lines_deleted": "regels verwijderd",
            "files_changed": "bestanden gewijzigd",
            "force_updated": "(Geforceerd bijgewerkt)",
        },
        "German": {
            "week_label": "Woche",
            "generated_on": "Generiert am",
            "commits_label": "Commits",
            "tech_changes": "🔧 Technische Änderungen",
            "user_impact": "📈 Benutzerauswirkung",
            "all_commits": "📋 Alle Commits",
            "statistics": "📊 Statistiken",
            "file_changes": "📁 Dateiänderungen",
            "changelog_title": "Changelog",
            "auto_updated": "Diese Datei wird automatisch mit wöchentlichen Änderungen aktualisiert.",
            "fallback_tech": "Diese Woche wurden technische Änderungen vorgenommen. Details siehe unten.",
            "fallback_business": "Diese Woche wurden verschiedene Verbesserungen und Updates implementiert.",
            "lines_added": "Zeilen hinzugefügt",
            "lines_deleted": "Zeilen gelöscht",
            "files_changed": "Dateien geändert",
            "force_updated": "(Erzwungen aktualisiert)",
        },
        "French": {
            "week_label": "Semaine",
            "generated_on": "Généré le",
            "commits_label": "commits",
            "tech_changes": "🔧 Modifications techniques",
            "user_impact": "📈 Impact utilisateur",
            "all_commits": "📋 Tous les commits",
            "statistics": "📊 Statistiques",
            "file_changes": "📁 Changements de fichiers",
            "changelog_title": "Journal des modifications",
            "auto_updated": "Ce fichier est automatiquement mis à jour avec les changements hebdomadaires.",
            "fallback_tech": "Des modifications techniques ont été apportées cette semaine. Voir les détails ci-dessous.",
            "fallback_business": "Diverses améliorations et mises à jour ont été implémentées cette semaine.",
            "lines_added": "lignes ajoutées",
            "lines_deleted": "lignes supprimées",
            "files_changed": "fichiers modifiés",
            "force_updated": "(Mise à jour forcée)",
        },
        "Spanish": {
            "week_label": "Semana",
            "generated_on": "Generado el",
            "commits_label": "commits",
            "tech_changes": "🔧 Cambios técnicos",
            "user_impact": "📈 Impacto del usuario",
            "all_commits": "📋 Todos los commits",
            "statistics": "📊 Estadísticas",
            "file_changes": "📁 Cambios en archivos",
            "changelog_title": "Registro de cambios",
            "auto_updated": "Este archivo se actualiza automáticamente con cambios semanales.",
            "fallback_tech": "Se realizaron cambios técnicos esta semana. Ver detalles de commits abajo.",
            "fallback_business": "Se implementaron varias mejoras y actualizaciones esta semana.",
            "lines_added": "líneas agregadas",
            "lines_deleted": "líneas eliminadas",
            "files_changed": "archivos cambiados",
            "force_updated": "(Actualización forzada)",
        },
    }

    if language not in language_configs:
        print(
            f"⚠️  Warning: Language '{language}' not supported. Falling back to English."
        )
        print(f"💡 Supported languages: {', '.join(language_configs.keys())}")
        return language_configs["English"]

    return language_configs[language]


def retry_api_call(
    max_retries: int = 3, delay: int = 2, timeout: int = 30
) -> Callable[[Callable[..., T]], Callable[..., T | None]]:
    """Decorator to retry API calls with exponential backoff, jitter, and rate limiting handling"""

    def decorator(func: Callable[..., T]) -> Callable[..., T | None]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T | None:
            import random

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e).lower()

                    # Handle rate limiting specifically
                    if (
                        "429" in error_str
                        or "rate limit" in error_str
                        or "too many requests" in error_str
                    ):
                        if attempt == max_retries - 1:
                            print(
                                f"❌ Rate limit exceeded after {max_retries} attempts."
                            )
                            print(
                                "💡 Suggestion: Try again in a few minutes, or consider using a different model with higher rate limits."
                            )
                            raise Exception(
                                f"Rate limit exceeded: {redact_api_key(str(e))}"
                            ) from e

                        # Longer wait for rate limiting with jitter
                        wait_time = delay * (3**attempt) + random.uniform(1, 5)
                        print(
                            f"⏰ Rate limit hit (attempt {attempt + 1}/{max_retries}). Waiting {wait_time:.1f}s before retry..."
                        )
                        time.sleep(wait_time)
                        continue

                    # Handle authentication errors
                    if (
                        "401" in error_str
                        or "unauthorized" in error_str
                        or "invalid api key" in error_str
                    ):
                        print(f"❌ Authentication failed: {redact_api_key(str(e))}")
                        print(
                            "💡 Please check your OPENROUTER_API_KEY secret is correctly set."
                        )
                        print("💡 Verify your API key at: https://openrouter.ai/keys")
                        raise Exception(
                            f"Authentication error: {redact_api_key(str(e))}"
                        ) from e

                    # Handle model not found errors
                    if (
                        "404" in error_str
                        or "model not found" in error_str
                        or "not available" in error_str
                    ):
                        print(f"❌ Model error: {redact_api_key(str(e))}")
                        print(
                            f"💡 The model '{os.getenv('MODEL', 'openai/gpt-5-mini')}' may not be available."
                        )
                        print(
                            "💡 Check available models at: https://openrouter.ai/models"
                        )
                        print(
                            "💡 Consider using 'openai/gpt-5-mini' or 'anthropic/claude-3-haiku' as alternatives."
                        )
                        raise Exception(
                            f"Model availability error: {redact_api_key(str(e))}"
                        ) from e

                    # Handle payload too large errors
                    if (
                        "413" in error_str
                        or "too large" in error_str
                        or "entity too large" in error_str
                    ):
                        print(f"❌ Request payload too large: {redact_api_key(str(e))}")
                        print(
                            "💡 The merge payload exceeds API limits. Hierarchical merge will be attempted."
                        )
                        raise Exception(
                            f"Payload too large error: {redact_api_key(str(e))}"
                        ) from e

                    # Handle network errors
                    if (
                        "timeout" in error_str
                        or "connection" in error_str
                        or "network" in error_str
                    ):
                        if attempt == max_retries - 1:
                            print(
                                f"❌ Network connectivity issues persisted after {max_retries} attempts."
                            )
                            print(
                                "💡 Check your internet connection and GitHub Actions network status."
                            )
                            raise Exception(
                                f"Network error: {redact_api_key(str(e))}"
                            ) from e

                        wait_time = delay * (2**attempt) + random.uniform(0.5, 2)
                        print(
                            f"🔌 Network issue (attempt {attempt + 1}/{max_retries}): {redact_api_key(str(e))}"
                        )
                        print(f"🔄 Retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        continue

                    # Generic error handling
                    if attempt == max_retries - 1:
                        print(f"❌ Final attempt failed: {redact_api_key(str(e))}")
                        print(
                            "💡 If this persists, check the action logs and consider:"
                        )
                        print("   - Reducing the days_back parameter")
                        print("   - Using a different model")
                        print("   - Checking OpenRouter service status")
                        raise

                    # Exponential backoff with jitter for other errors
                    wait_time = delay * (2**attempt) + random.uniform(0.1, 1)
                    print(
                        f"⚠️  API call failed (attempt {attempt + 1}/{max_retries}): {redact_api_key(str(e))}"
                    )
                    print(f"🔄 Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
            return None

        return wrapper

    return decorator


def cleanup_temp_files() -> None:
    """Clean up temporary files to free memory"""
    temp_files = [
        "commits.txt",
        "commits_extended.txt",
        "files_changed.txt",
        "lines_added.tmp",
        "lines_deleted.tmp",
    ]
    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except OSError as e:
            print(f"Warning: Could not remove temp file {temp_file}: {e}")


def get_chunk_cache_key(
    chunk_commits_text: str, summary_type: str, model: str, output_language: str
) -> str:
    """Generate deterministic cache key for chunk summaries.

    Args:
        chunk_commits_text: Text of commits in the chunk
        summary_type: "technical" or "business"
        model: Model name used for generation
        output_language: Language for output

    Returns:
        16-character hex string cache key
    """
    content = f"{chunk_commits_text}|{summary_type}|{model}|{output_language}"
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def get_chunk_cache_dir() -> str:
    """Get chunk cache directory path and ensure it exists.

    Returns:
        Path to chunk cache directory
    """
    cache_dir = os.path.join(tempfile.gettempdir(), "changelog_cache", "chunks")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def read_chunk_cache(cache_key: str) -> str | None:
    """Read cached chunk summary from disk.

    Args:
        cache_key: Cache key for the chunk

    Returns:
        Cached content or None if not found/empty
    """
    cache_dir = get_chunk_cache_dir()
    cache_file = os.path.join(cache_dir, f"{cache_key}.txt")

    try:
        if os.path.exists(cache_file):
            with open(cache_file, encoding="utf-8") as f:
                content = f.read().strip()
                return content if content else None
    except (OSError, UnicodeDecodeError) as e:
        print(f"⚠️  Warning: Could not read cache file {cache_key}: {e}")

    return None


def write_chunk_cache(cache_key: str, content: str) -> None:
    """Write chunk summary to cache.

    Args:
        cache_key: Cache key for the chunk
        content: Summary content to cache
    """
    cache_dir = get_chunk_cache_dir()
    cache_file = os.path.join(cache_dir, f"{cache_key}.txt")

    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as e:
        print(f"⚠️  Warning: Could not write cache file {cache_key}: {e}")


def cleanup_chunk_cache(max_age_hours: int = 48) -> None:
    """Remove stale chunk cache files older than max_age_hours.

    Args:
        max_age_hours: Maximum age in hours before cache files are removed
    """
    cache_dir = get_chunk_cache_dir()
    max_age_seconds = max_age_hours * 3600
    current_time = time.time()
    removed_count = 0

    try:
        for filename in os.listdir(cache_dir):
            if filename.endswith(".txt"):
                file_path = os.path.join(cache_dir, filename)
                try:
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        os.remove(file_path)
                        removed_count += 1
                except OSError:
                    pass  # Skip files we can't access
    except OSError:
        pass  # Directory doesn't exist or can't be read

    if removed_count > 0:
        print(f"🧹 Cleaned up {removed_count} stale chunk cache files")


if __name__ == "__main__":
    # Clean up old chunk cache files at startup
    cleanup_chunk_cache(max_age_hours=48)

    # Check if API key is present with detailed guidance
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in environment")
        print("💡 To fix this issue:")
        print("   1. Go to your repository Settings > Secrets and variables > Actions")
        print("   2. Click 'New repository secret'")
        print("   3. Name: OPENROUTER_API_KEY")
        print("   4. Value: Your API key from https://openrouter.ai/keys")
        print(
            "   5. Make sure your workflow uses: openrouter_api_key: ${{ secrets.OPENROUTER_API_KEY }}"
        )
        sys.exit(1)

    # Validate API key format (basic check)
    if not api_key.startswith("sk-or-"):
        print(
            "⚠️  Warning: API key doesn't match expected OpenRouter format (should start with 'sk-or-')"
        )
        print(
            "💡 If you're getting authentication errors, verify your key at: https://openrouter.ai/keys"
        )

    # Configure OpenAI client for OpenRouter with timeout
    client = OpenAI(
        api_key=api_key, base_url="https://openrouter.ai/api/v1", timeout=30.0
    )

    model = os.getenv("MODEL", "openai/gpt-5-mini")
    output_language = os.getenv("OUTPUT_LANGUAGE", "English")
    force_update = os.getenv("FORCE_UPDATE", "false").lower() == "true"
    extended_analysis = os.getenv("EXTENDED_ANALYSIS", "false").lower() == "true"
    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"

    print(f"🤖 Using model: {model}")
    print(f"🌍 Output language: {output_language}")
    print(f"🔧 Force update: {force_update}")
    print(f"🧪 Dry run mode: {dry_run}")
    print(f"🔍 Extended analysis: {extended_analysis}")

    # Get language-specific configuration
    config = get_language_config(output_language)

    # Read commits
    try:
        with open("commits.txt", encoding="utf-8") as f:
            commits_raw = f.read().strip()
    except FileNotFoundError:
        print("❌ commits.txt not found")
        sys.exit(1)

    if not commits_raw:
        print("ℹ️  No commits to process")
        sys.exit(0)

    # Read extended data if available
    extended_data = ""
    file_changes_data = ""

    if extended_analysis:
        try:
            # Read detailed commit info
            if os.path.exists("commits_extended.txt"):
                with open("commits_extended.txt", encoding="utf-8") as f:
                    extended_data = f.read().strip()

            # Read file changes
            if os.path.exists("files_changed.txt"):
                with open("files_changed.txt", encoding="utf-8") as f:
                    files_list = f.read().strip().split("\n")
                    # Group files by type/directory
                    file_groups: dict[str, list[str]] = {}
                    for file_path in files_list:
                        if file_path:
                            # Get file extension or directory
                            if "." in file_path:
                                ext = file_path.split(".")[-1].lower()
                                key = f"*.{ext} files"
                            else:
                                key = "Config/Other files"

                            if key not in file_groups:
                                file_groups[key] = []
                            file_groups[key].append(file_path)

                    file_changes_summary = []
                    for group, files in sorted(file_groups.items()):
                        # Only show count if more than 3 files, otherwise show names
                        if len(files) <= 3:
                            file_changes_summary.append(
                                f"**{group}**: {', '.join(files)}"
                            )
                        else:
                            # Show count + first 2 examples only (prevents oversized prompts)
                            examples = ", ".join(files[:2])
                            file_changes_summary.append(
                                f"**{group}** ({len(files)} files): {examples}, ..."
                            )

                    file_changes_data = "\n".join(file_changes_summary)
        except (OSError, FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
            print(
                f"⚠️  Warning: Extended analysis data unavailable ({type(e).__name__}): {e}"
            )

    @retry_api_call(max_retries=3, delay=2, timeout=30)
    def merge_chunk_summaries(chunk_summaries, summary_type, total_commits, num_chunks):
        """Merge multiple chunk summaries into a single cohesive summary"""
        print(f"🔄 Merging {num_chunks} {summary_type} chunk summaries...")

        combined_chunks = "\n\n---\n\n".join(
            [f"Chunk {i + 1}:\n{summary}" for i, summary in enumerate(chunk_summaries)]
        )

        merge_prompt = textwrap.dedent(f"""
    You are merging multiple changelog summaries into a single cohesive summary.

    You have {num_chunks} summaries covering {total_commits} total commits.

    Here are the individual chunk summaries:

    {combined_chunks}

    Your task: Create ONE unified, well-structured summary that:
    1. Combines all information from the chunks
    2. Removes duplicates and redundant information
    3. Organizes content logically by category
    4. Maintains proper markdown formatting with headers and bullets
    5. Is comprehensive and covers all significant changes
    6. Flows naturally as a single document

    Ensure output starts directly with content (no ### level headers). Use #### for sub-sections.
    Use the same structure and formatting as the individual chunks.
    Language: {output_language}

    Generate the merged {summary_type}:
    """).strip()

        # Check prompt size and truncate if needed (safety net for 413 errors)
        MAX_MERGE_PROMPT_CHARS = 100000  # ~25K tokens, safe limit for most models
        if len(merge_prompt) > MAX_MERGE_PROMPT_CHARS:
            print(
                f"⚠️  Merge prompt too large ({len(merge_prompt)} chars), truncating to {MAX_MERGE_PROMPT_CHARS}"
            )
            merge_prompt = (
                merge_prompt[:MAX_MERGE_PROMPT_CHARS]
                + "\n\n[Some chunk summaries truncated due to size limits]"
            )

        # Validate request size before sending (fail fast with clear error)
        estimated_tokens = len(merge_prompt) // 4
        if estimated_tokens > 120000:  # Most models have 128K context limit
            raise ValueError(
                f"Merge prompt too large (~{estimated_tokens} tokens). Consider using smaller batch_size in hierarchical merge."
            )

        if estimated_tokens > 30000:
            print(f"⚠️  Warning: Large merge payload (~{estimated_tokens} tokens)")

        # Use higher token limit for merging
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert technical writer who creates comprehensive, well-organized summaries.",
                },
                {"role": "user", "content": merge_prompt},
            ],
            max_tokens=6000,  # Higher limit for merged output
            temperature=0.3,
            extra_headers={
                "HTTP-Referer": f"https://github.com/{os.getenv('GITHUB_REPOSITORY', 'unknown')}",
                "X-Title": "Weekly-Changelog-Generator",
            },
        )

        content = response.choices[0].message.content
        merged_summary = content.strip() if content else ""

        if not merged_summary or len(merged_summary) < 50:
            raise ValueError(f"Merged {summary_type} too short or empty")

        return merged_summary

    def hierarchical_merge_summaries(
        chunk_summaries, summary_type, total_commits, batch_size=5
    ):
        """
        Merge summaries hierarchically to avoid 413 errors.

        Instead of merging all chunks at once, merge in batches of batch_size,
        then recursively merge the results until we have a single summary.
        """
        num_summaries = len(chunk_summaries)

        if num_summaries <= 1:
            return chunk_summaries[0] if chunk_summaries else ""

        # If we have few enough summaries, try direct merge
        if num_summaries <= batch_size:
            try:
                return merge_chunk_summaries(
                    chunk_summaries, summary_type, total_commits, num_summaries
                )
            except Exception as e:
                if "413" in str(e) or "too large" in str(e).lower():
                    # Reduce batch size and retry
                    if batch_size > 2:
                        print(
                            f"⚠️ Payload too large with batch_size={batch_size}, reducing to {batch_size - 1}"
                        )
                        return hierarchical_merge_summaries(
                            chunk_summaries, summary_type, total_commits, batch_size - 1
                        )
                raise

        # Merge in batches
        print(
            f"🔄 Hierarchical merge: {num_summaries} summaries in batches of {batch_size}"
        )
        merged_batches = []

        for i in range(0, num_summaries, batch_size):
            batch = chunk_summaries[i : i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (num_summaries + batch_size - 1) // batch_size
            print(
                f"  📦 Merging batch {batch_num}/{total_batches} ({len(batch)} summaries)"
            )

            try:
                merged = merge_chunk_summaries(
                    batch, summary_type, total_commits, len(batch)
                )
                merged_batches.append(merged)
            except Exception as e:
                if "413" in str(e) or "too large" in str(e).lower():
                    # Try with smaller batch
                    print("  ⚠️ Batch too large, splitting further")
                    for sub_batch in [
                        batch[: len(batch) // 2],
                        batch[len(batch) // 2 :],
                    ]:
                        if sub_batch:
                            sub_merged = hierarchical_merge_summaries(
                                sub_batch,
                                summary_type,
                                total_commits,
                                max(2, batch_size - 2),
                            )
                            merged_batches.append(sub_merged)
                else:
                    raise

        # Recursively merge the merged batches
        return hierarchical_merge_summaries(
            merged_batches, summary_type, total_commits, batch_size
        )

    # Process commits with chunking for large sets
    repo_url = f"https://github.com/{os.getenv('GITHUB_REPOSITORY', 'unknown')}"
    commits_formatted, commit_links = process_commits_in_chunks(commits_raw, repo_url)
    total_commits = len(commits_formatted)

    # Commit count validation and diagnostics
    days_back = os.getenv("DAYS_BACK", "7")
    print(
        f"📊 Validation: Processing {total_commits} commits for {days_back}-day period"
    )

    # Warn if commit count seems unusually low
    if total_commits > 0:
        expected_min_commits = (
            int(days_back) // 7
        )  # Very conservative estimate (1 commit per week)
        if total_commits < expected_min_commits:
            print(
                f"⚠️  Warning: Only found {total_commits} commits for {days_back} days - this may indicate:"
            )
            print("   - Git fetch depth limitation (increase fetch-depth in workflow)")
            print("   - Actual low activity period")
            print("   - Git filters may be too aggressive")

    # Intelligent chunking system for large commit sets
    COMMITS_PER_CHUNK = 5  # Small chunks for highly detailed analysis
    # Limit concurrent chunk processing to avoid rate limiting
    # Higher = faster but more likely to hit 429 errors; Lower = slower but more reliable
    MAX_CONCURRENT_CHUNKS = 3
    use_chunking = total_commits > COMMITS_PER_CHUNK
    num_chunks = 0
    chunks_info = ""

    if use_chunking:
        num_chunks = (
            total_commits + COMMITS_PER_CHUNK - 1
        ) // COMMITS_PER_CHUNK  # Ceiling division
        print(f"📊 Large commit set detected ({total_commits} commits)")
        print(
            f"🔄 Will analyze in {num_chunks} chunks of ~{COMMITS_PER_CHUNK} commits each for detailed analysis"
        )
        print(
            "💡 This approach ensures each commit gets focused attention before merging into comprehensive summary"
        )
        chunks_info = f"\n\n> 📊 **Note**: This changelog was generated by analyzing {total_commits} commits across {num_chunks} detailed chunks for comprehensive, high-quality coverage."
    else:
        print(f"✅ Processing all {total_commits} commits in a single analysis")

    commits_links_text = "\n".join(commit_links)

    # Build base context for extended analysis (used in all chunks)
    extended_context = ""
    if extended_analysis and extended_data:
        extended_context = "\n\nDetailed file changes and statistics are also available for deeper analysis."
        if file_changes_data:
            # Limit file changes data to prevent oversized prompts (413 errors)
            MAX_FILE_CHANGES_CHARS = 5000
            if len(file_changes_data) > MAX_FILE_CHANGES_CHARS:
                print(
                    f"⚠️  File changes data truncated ({len(file_changes_data)} -> {MAX_FILE_CHANGES_CHARS} chars)"
                )
                file_changes_data = (
                    file_changes_data[:MAX_FILE_CHANGES_CHARS] + "\n... (truncated)"
                )
            extended_context += f"\n\nFile changes summary:\n{file_changes_data}"

    # Prompt templates: concise for small commit sets, full for larger ones
    extended_focus = (
        " - Focus on the most significant changes and their technical implications based on file statistics"
        if extended_analysis
        else ""
    )
    extended_scope = (
        " - Consider the overall scope and significance based on the extent of changes"
        if extended_analysis
        else ""
    )

    if total_commits <= 5:
        # Concise prompts for small commit sets — no empty category filler
        tech_prompt_template = textwrap.dedent(f"""
You are a senior software developer writing a technical changelog for a development team.

Analyze these commits and create a concise technical summary in {output_language}:

{{base_context}}

Create a structured technical summary. Start directly with content (no top-level ### header).

Write a 1-2 sentence overview of the changes, then list each change as a bullet point with specific details about what was changed and why. Use #### headers only if there are multiple distinct categories of changes. Skip categories with no relevant changes.

Requirements:
- Start directly with the overview text (no ### header)
- Use #### for sub-sections only when needed
- Use bullet lists (-) for all items
- Be concise — only include relevant categories
- Provide specific details about what was changed and why
{extended_focus}

Write in a clear, structured format with proper markdown formatting.
""").strip()

        business_prompt_template = textwrap.dedent(f"""
You are a product manager communicating updates to stakeholders and end users.

Translate these technical commits into business impact in {output_language}:

{{base_context}}

Create a business-focused summary. Start directly with content (no top-level ### header).

Write a 2-3 sentence overview for a non-technical audience, then list key impacts as bullet points. Only include sections that are relevant to the actual changes. Skip sections with no relevant impact.

Requirements:
- Start directly with the overview text (no ### header)
- Use #### for sub-sections only when needed
- Use bullet lists (-) for all items
- Avoid technical jargon and implementation details
- Focus on benefits, outcomes, and user value
- Be concise — only include relevant sections
{extended_scope}

Write in a clear, business-focused style with proper markdown formatting.
""").strip()

    else:
        # Full prompts for larger commit sets
        tech_prompt_template = textwrap.dedent(f"""
You are a senior software developer writing a technical changelog for a development team.

Analyze these commits and create a structured technical summary in {output_language}:

{{base_context}}

Create a structured technical summary. Start directly with content (no top-level ### header):

[Write 1-2 sentence overview of the week's development activity]

#### Main Changes by Category

**Features:**
- [List each new feature added as a bullet point]
- [Be specific about what functionality was added]

**Bug Fixes:**
- [List each bug fix as a bullet point]
- [Mention what issue was resolved]

**Refactoring:**
- [List code improvements and restructuring]
- [Explain what was cleaned up or optimized]

**Infrastructure/DevOps:**
- [List build, deployment, and tooling changes]

**Documentation:**
- [List documentation updates]

**Testing:**
- [List test additions and improvements]

#### Technical Highlights
- [Key architectural decisions made]
- [Performance improvements implemented]
- [Security enhancements added]

Requirements:
- Start directly with the overview text (no ### header)
- Use #### for sub-sections
- Use bold text (**text:**) for category labels
- Use bullet lists (-) for all items
- Skip categories with no relevant changes
- Provide specific details about what was changed and why
{extended_focus}

Write in a clear, structured format with proper markdown formatting.
""").strip()

        business_prompt_template = textwrap.dedent(f"""
You are a product manager communicating updates to stakeholders and end users.

Translate these technical commits into business impact in {output_language}:

{{base_context}}

Create a business-focused summary. Start directly with content (no top-level ### header):

[Write 2-3 sentence overview for non-technical audience explaining what was accomplished this week]

#### User Experience Impact
- [How these changes affect what users see and experience]

#### Business Benefits
- [Value delivered to the organization]

#### Performance & Reliability
- [Improvements in system speed or responsiveness]

#### New Capabilities
- [New features or functionality now available]

#### Important Changes to Note
- [Breaking changes or significant updates users should be aware of]

Requirements:
- Start directly with the overview text (no ### header)
- Use #### for sub-sections
- Use bullet lists (-) for all items
- Skip sections with no relevant changes
- Avoid technical jargon and implementation details
- Focus on benefits, outcomes, and user value
{extended_scope}

Write in a clear, business-focused style with proper markdown formatting.
""").strip()

    @retry_api_call(max_retries=3, delay=2, timeout=30)
    def generate_summary(prompt, description, chunk_number=None):
        """Generate a single summary (technical or business) with proper markdown formatting"""
        chunk_info = f" (chunk {chunk_number})" if chunk_number else ""
        print(f"🔄 Generating {description}{chunk_info}...")

        # Check prompt size and truncate if needed (safety net for 413 errors)
        MAX_PROMPT_CHARS = 100000  # ~25K tokens, safe limit for most models
        if len(prompt) > MAX_PROMPT_CHARS:
            print(
                f"⚠️  Prompt too large ({len(prompt)} chars), truncating to {MAX_PROMPT_CHARS}"
            )
            # Keep the beginning (template + commits) and truncate extended data at the end
            prompt = (
                prompt[:MAX_PROMPT_CHARS]
                + "\n\n[Extended data truncated due to size limits]"
            )

        # Validate request size before sending (fail fast with clear error)
        estimated_tokens = len(prompt) // 4
        if estimated_tokens > 120000:  # Most models have 128K context limit
            raise ValueError(
                f"Prompt too large (~{estimated_tokens} tokens). Consider reducing extended analysis data or days_back parameter."
            )

        # Significantly increased token limits for comprehensive summaries
        # Dynamic scaling based on extended analysis and commit count
        if extended_analysis:
            max_tokens = 6000
        elif total_commits > 100:
            max_tokens = 5000
        else:
            max_tokens = 3000

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an experienced technical writer who creates clear, structured summaries with proper markdown formatting.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.3,
            extra_headers={
                "HTTP-Referer": f"https://github.com/{os.getenv('GITHUB_REPOSITORY', 'unknown')}",
                "X-Title": "Weekly-Changelog-Generator",
            },
        )

        # Validate response
        content = response.choices[0].message.content
        response_content = content.strip() if content else ""

        if not response_content or len(response_content) < 50:
            raise ValueError(f"AI response too short or empty for {description}")

        # Validate has markdown formatting
        if "###" not in response_content and "**" not in response_content:
            print(
                f"⚠️  Warning: {description} may be poorly formatted (missing markdown headers)"
            )

        return response_content

    def generate_chunked_summary(
        commits_list, prompt_template, description, summary_type
    ):
        """Generate summary by processing commits in chunks and merging results"""
        if not use_chunking:
            # No chunking needed, process all commits at once
            commits_text = "\n".join(commits_list)
            base_context = f"Commits:\n{commits_text}{extended_context}"
            prompt = prompt_template.format(base_context=base_context)
            return generate_summary(prompt, description)

        # Track cache statistics
        cache_hits = 0
        cache_misses = 0

        # Process chunks in parallel with rate-limit-aware concurrency
        def process_chunk(chunk_idx):
            """Process a single chunk and return (index, summary, cache_hit)"""
            nonlocal cache_hits, cache_misses

            start_idx = chunk_idx * COMMITS_PER_CHUNK
            end_idx = min(start_idx + COMMITS_PER_CHUNK, total_commits)
            chunk_commits = commits_list[start_idx:end_idx]

            commits_text = "\n".join(chunk_commits)

            # Check cache first
            cache_key = get_chunk_cache_key(
                commits_text, summary_type, model, output_language
            )
            cached_summary = read_chunk_cache(cache_key)

            if cached_summary:
                print(
                    f"   💾 Cache hit for chunk {chunk_idx + 1}/{num_chunks} {description}"
                )
                cache_hits += 1
                return (chunk_idx, cached_summary, True)

            # Cache miss - generate new summary
            cache_misses += 1
            base_context = f"Commits (chunk {chunk_idx + 1} of {num_chunks}, commits {start_idx + 1}-{end_idx}):\n{commits_text}{extended_context}"

            prompt = prompt_template.format(base_context=base_context)

            try:
                chunk_summary = generate_summary(
                    prompt, description, chunk_number=chunk_idx + 1
                )
                # Write to cache
                if chunk_summary is not None:
                    write_chunk_cache(cache_key, chunk_summary)
                print(f"✅ Chunk {chunk_idx + 1}/{num_chunks} {description} completed")
                return (chunk_idx, chunk_summary, False)
            except Exception as e:
                print(
                    f"⚠️  Warning: Failed to generate {description} for chunk {chunk_idx + 1}: {e}"
                )
                # Continue with other chunks even if one fails
                fallback = f"[Chunk {chunk_idx + 1} analysis failed - commits {start_idx + 1}-{end_idx} not included in detail]"
                return (chunk_idx, fallback, False)

        # Use ThreadPoolExecutor to process chunks concurrently
        chunk_summaries_dict = {}
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=MAX_CONCURRENT_CHUNKS
        ) as executor:
            # Submit all chunks
            futures = [
                executor.submit(process_chunk, chunk_idx)
                for chunk_idx in range(num_chunks)
            ]

            # Collect results maintaining order
            for future in concurrent.futures.as_completed(futures):
                chunk_idx, chunk_summary, was_cached = future.result()
                chunk_summaries_dict[chunk_idx] = chunk_summary

        # Convert dict to ordered list
        chunk_summaries = [chunk_summaries_dict[i] for i in range(num_chunks)]

        # Print cache statistics
        print(
            f"   📊 Cache: {cache_hits} hits, {cache_misses} misses out of {num_chunks} chunks"
        )

        # Merge all chunk summaries
        if len(chunk_summaries) == 1:
            return chunk_summaries[0]
        elif len(chunk_summaries) > 1:
            return hierarchical_merge_summaries(
                chunk_summaries, summary_type, total_commits
            )
        else:
            raise Exception(f"No {description} chunks were successfully generated")

    # Generate summaries with intelligent chunking and fallback
    # Run tech and business summary generation in parallel
    tech_summary = None
    business_summary = None

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both summary generation tasks
        tech_future = executor.submit(
            generate_chunked_summary,
            commits_formatted,
            tech_prompt_template,
            "technical summary",
            "technical",
        )
        business_future = executor.submit(
            generate_chunked_summary,
            commits_formatted,
            business_prompt_template,
            "business summary",
            "business",
        )

        # Collect results with individual error handling
        try:
            tech_summary = tech_future.result()
            print("✅ Technical summary generated successfully")
        except Exception as e:
            print(
                f"⚠️  Using fallback for technical summary due to: {redact_api_key(str(e))}"
            )
            tech_summary = config["fallback_tech"]

        try:
            business_summary = business_future.result()
            print("✅ Business summary generated successfully")
        except Exception as e:
            print(
                f"⚠️  Using fallback for business summary due to: {redact_api_key(str(e))}"
            )
            business_summary = config["fallback_business"]

    # Calculate week and year
    today = datetime.date.today()
    week_num = today.isocalendar()[1]
    year = today.year

    # Format date according to language
    date_formats = {
        "English": "%m-%d-%Y",
        "Dutch": "%d-%m-%Y",
        "German": "%d.%m.%Y",
        "French": "%d/%m/%Y",
        "Spanish": "%d/%m/%Y",
    }
    date_format = date_formats.get(output_language, "%m-%d-%Y")
    formatted_date = today.strftime(date_format)

    # Check for duplicate entries and handle force mode
    changelog_path = "CHANGELOG.md"
    week_header = f"## {config['week_label']} {week_num}, {year}"
    force_suffix = f" {config['force_updated']}" if force_update else ""

    try:
        if os.path.exists(changelog_path):
            with open(changelog_path, encoding="utf-8") as f:
                existing_content = f.read()

            if week_header in existing_content and not force_update:
                print(
                    f"⚠️  Entry for {config['week_label']} {week_num}, {year} already exists. Use force=true to update anyway."
                )
                sys.exit(0)
            elif week_header in existing_content and force_update:
                print(
                    f"🔧 Force mode: Updating existing entry for {config['week_label']} {week_num}, {year}"
                )
                # Remove existing entry
                lines = existing_content.split("\n")
                new_lines = []
                skip_section = False

                for line in lines:
                    if line.startswith(week_header):
                        skip_section = True
                        continue
                    elif line.startswith("## ") and skip_section:
                        skip_section = False
                        new_lines.append(line)
                    elif line.startswith("---") and skip_section:
                        skip_section = False
                        continue
                    elif not skip_section:
                        new_lines.append(line)

                existing_content = "\n".join(new_lines)
        else:
            existing_content = (
                f"# {config['changelog_title']}\n\n{config['auto_updated']}\n"
            )

        # Prepare statistics section for extended analysis
        stats_section = ""
        if extended_analysis:
            lines_added = os.getenv("LINES_ADDED", "0")
            lines_deleted = os.getenv("LINES_DELETED", "0")
            files_changed = os.getenv("FILES_CHANGED", "0")

            stats_parts = [
                "",
                f"### {config['statistics']}",
                f"- **{lines_added}** {config['lines_added']}",
                f"- **{lines_deleted}** {config['lines_deleted']}",
                f"- **{files_changed}** {config['files_changed']}",
            ]
            if file_changes_data:
                stats_parts.extend(
                    ["", f"### {config['file_changes']}", file_changes_data]
                )
            stats_section = "\n".join(stats_parts)

        # Create changelog entry with chunking info if applicable
        entry_parts = [
            f"{week_header}{force_suffix}",
            "",
            f"*{config['generated_on']} {formatted_date} - {len(commits_formatted)} {config['commits_label']}*",
        ]
        if chunks_info:
            entry_parts.append(chunks_info.strip())
        entry_parts.extend(
            [
                "",
                f"### {config['tech_changes']}",
                tech_summary,
                "",
                f"### {config['user_impact']}",
                business_summary,
            ]
        )
        if stats_section:
            entry_parts.append(stats_section)
        entry_parts.extend(
            [
                "",
                f"### {config['all_commits']}",
                commits_links_text,
                "",
                "---",
            ]
        )
        changelog_entry = "\n".join(entry_parts)

        # Prepend new entry to the changelog (after header)
        lines = existing_content.split("\n")
        header_end = 0

        # Find where to insert (after the main header and description)
        for i, line in enumerate(lines):
            if line.startswith("# ") or line.strip() == config["auto_updated"]:
                header_end = i + 1
            elif line.startswith("## ") or (
                i > 0 and lines[i - 1].strip() == config["auto_updated"]
            ):
                break

        # Insert the new entry
        new_lines = lines[:header_end] + ["", changelog_entry, ""] + lines[header_end:]
        new_content = "\n".join(new_lines)

        # Write updated changelog
        with open(changelog_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        action = "updated (forced)" if force_update else "updated"
        print(f"✅ Changelog {action} for {config['week_label']} {week_num}, {year}")

    except Exception as e:
        print(f"❌ Error writing changelog: {redact_api_key(str(e))}")
        print("💡 Common causes:")
        print("   - File permissions issue")
        print("   - Disk space issue")
        print("   - Invalid markdown content")
        cleanup_temp_files()
        sys.exit(1)

    finally:
        # Clean up temporary files
        cleanup_temp_files()
        print("🧹 Cleaned up temporary files")
