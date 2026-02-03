import os
import sys
import datetime
import textwrap
import time
import re
from functools import wraps
from openai import OpenAI

def retry_api_call(max_retries=3, delay=2, timeout=30):
    """Decorator to retry API calls with exponential backoff, jitter, and rate limiting handling"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            import random
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_str = str(e).lower()
                    
                    # Handle rate limiting specifically
                    if "429" in error_str or "rate limit" in error_str or "too many requests" in error_str:
                        if attempt == max_retries - 1:
                            print(f"❌ Rate limit exceeded after {max_retries} attempts.")
                            print(f"💡 Suggestion: Try again in a few minutes, or consider using a different model with higher rate limits.")
                            raise Exception(f"Rate limit exceeded: {str(e)}")
                        
                        # Longer wait for rate limiting with jitter
                        wait_time = delay * (3 ** attempt) + random.uniform(1, 5)
                        print(f"⏰ Rate limit hit (attempt {attempt + 1}/{max_retries}). Waiting {wait_time:.1f}s before retry...")
                        time.sleep(wait_time)
                        continue
                    
                    # Handle authentication errors
                    if "401" in error_str or "unauthorized" in error_str or "invalid api key" in error_str:
                        print(f"❌ Authentication failed: {str(e)}")
                        print(f"💡 Please check your OPENROUTER_API_KEY secret is correctly set.")
                        print(f"💡 Verify your API key at: https://openrouter.ai/keys")
                        raise Exception(f"Authentication error: {str(e)}")
                    
                    # Handle model not found errors
                    if "404" in error_str or "model not found" in error_str or "not available" in error_str:
                        print(f"❌ Model error: {str(e)}")
                        print(f"💡 The model '{os.getenv('MODEL', 'openai/gpt-5-mini')}' may not be available.")
                        print(f"💡 Check available models at: https://openrouter.ai/models")
                        print(f"💡 Consider using 'openai/gpt-5-mini' or 'anthropic/claude-3-haiku' as alternatives.")
                        raise Exception(f"Model availability error: {str(e)}")

                    # Handle payload too large errors
                    if "413" in error_str or "too large" in error_str or "entity too large" in error_str:
                        print(f"❌ Request payload too large: {str(e)}")
                        print(f"💡 The merge payload exceeds API limits. Hierarchical merge will be attempted.")
                        raise Exception(f"Payload too large error: {str(e)}")
                    
                    # Handle network errors
                    if "timeout" in error_str or "connection" in error_str or "network" in error_str:
                        if attempt == max_retries - 1:
                            print(f"❌ Network connectivity issues persisted after {max_retries} attempts.")
                            print(f"💡 Check your internet connection and GitHub Actions network status.")
                            raise Exception(f"Network error: {str(e)}")
                        
                        wait_time = delay * (2 ** attempt) + random.uniform(0.5, 2)
                        print(f"🔌 Network issue (attempt {attempt + 1}/{max_retries}): {str(e)}")
                        print(f"🔄 Retrying in {wait_time:.1f}s...")
                        time.sleep(wait_time)
                        continue
                    
                    # Generic error handling
                    if attempt == max_retries - 1:
                        print(f"❌ Final attempt failed: {str(e)}")
                        print(f"💡 If this persists, check the action logs and consider:")
                        print(f"   - Reducing the days_back parameter")
                        print(f"   - Using a different model")
                        print(f"   - Checking OpenRouter service status")
                        raise
                    
                    # Exponential backoff with jitter for other errors
                    wait_time = delay * (2 ** attempt) + random.uniform(0.1, 1)
                    print(f"⚠️  API call failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    print(f"🔄 Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
            return None
        return wrapper
    return decorator

# Check if API key is present with detailed guidance
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("❌ OPENROUTER_API_KEY not found in environment")
    print("💡 To fix this issue:")
    print("   1. Go to your repository Settings > Secrets and variables > Actions")
    print("   2. Click 'New repository secret'")
    print("   3. Name: OPENROUTER_API_KEY")
    print("   4. Value: Your API key from https://openrouter.ai/keys")
    print("   5. Make sure your workflow uses: openrouter_api_key: ${{ secrets.OPENROUTER_API_KEY }}")
    sys.exit(1)

# Validate API key format (basic check)
if not api_key.startswith('sk-or-'):
    print("⚠️  Warning: API key doesn't match expected OpenRouter format (should start with 'sk-or-')")
    print("💡 If you're getting authentication errors, verify your key at: https://openrouter.ai/keys")

# Configure OpenAI client for OpenRouter with timeout
client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1",
    timeout=30.0
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

# Language-specific configurations
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
        "force_updated": "(Force Updated)"
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
        "fallback_business": "Verschillende verbeteringen en updates zijn deze week geïmplementeerd.",
        "lines_added": "regels toegevoegd",
        "lines_deleted": "regels verwijderd",
        "files_changed": "bestanden gewijzigd",
        "force_updated": "(Geforceerd bijgewerkt)"
    },
    "German": {
        "week_label": "Woche",
        "generated_on": "Generiert am",
        "commits_label": "Commits",
        "tech_changes": "🔧 Technische Änderungen",
        "user_impact": "📈 Auswirkungen für Benutzer",
        "all_commits": "📋 Alle Commits",
        "statistics": "📊 Statistiken",
        "file_changes": "📁 Dateiänderungen",
        "changelog_title": "Changelog",
        "auto_updated": "Diese Datei wird automatisch mit wöchentlichen Änderungen aktualisiert.",
        "fallback_tech": "Diese Woche wurden technische Änderungen vorgenommen. Details siehe Commits unten.",
        "fallback_business": "Verschiedene Verbesserungen und Updates wurden diese Woche implementiert.",
        "lines_added": "Zeilen hinzugefügt",
        "lines_deleted": "Zeilen gelöscht",
        "files_changed": "Dateien geändert",
        "force_updated": "(Zwangsweise aktualisiert)"
    },
    "French": {
        "week_label": "Semaine",
        "generated_on": "Généré le",
        "commits_label": "commits",
        "tech_changes": "🔧 Modifications techniques",
        "user_impact": "📈 Impact utilisateur",
        "all_commits": "📋 Tous les commits",
        "statistics": "📊 Statistiques",
        "file_changes": "📁 Modifications de fichiers",
        "changelog_title": "Journal des modifications",
        "auto_updated": "Ce fichier est automatiquement mis à jour avec les modifications hebdomadaires.",
        "fallback_tech": "Des modifications techniques ont été apportées cette semaine. Voir les détails des commits ci-dessous.",
        "fallback_business": "Diverses améliorations et mises à jour ont été implémentées cette semaine.",
        "lines_added": "lignes ajoutées",
        "lines_deleted": "lignes supprimées",
        "files_changed": "fichiers modifiés",
        "force_updated": "(Mise à jour forcée)"
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
        "force_updated": "(Actualización forzada)"
    }
}

config = language_configs.get(output_language, language_configs["English"])

# Read commits
try:
    with open("commits.txt", "r", encoding="utf-8") as f:
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
            with open("commits_extended.txt", "r", encoding="utf-8") as f:
                extended_data = f.read().strip()
        
        # Read file changes
        if os.path.exists("files_changed.txt"):
            with open("files_changed.txt", "r", encoding="utf-8") as f:
                files_list = f.read().strip().split('\n')
                # Group files by type/directory
                file_groups = {}
                for file_path in files_list:
                    if file_path:
                        # Get file extension or directory
                        if '.' in file_path:
                            ext = file_path.split('.')[-1].lower()
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
                        file_changes_summary.append(f"**{group}**: {', '.join(files)}")
                    else:
                        # Show count + first 2 examples only (prevents oversized prompts)
                        examples = ', '.join(files[:2])
                        file_changes_summary.append(f"**{group}** ({len(files)} files): {examples}, ...")

                file_changes_data = '\n'.join(file_changes_summary)
    except Exception as e:
        print(f"⚠️  Could not read extended data: {e}")

# Format commits for better readability with streaming support
commits_formatted = []
commit_links = []
repo_url = f"https://github.com/{os.getenv('GITHUB_REPOSITORY', 'unknown')}"

def process_commits_in_chunks(commits_raw, chunk_size=50):
    """Process commits in chunks to handle large commit sets efficiently"""
    lines = commits_raw.strip().split('\n')
    local_commits_formatted = []
    local_commit_links = []
    
    # Process in smaller chunks to manage memory for very large sets
    for i in range(0, len(lines), chunk_size):
        chunk = lines[i:i + chunk_size]
        
        for line in chunk:
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 5:
                    full_hash, subject, author, date, short_hash = parts[:5]
                    local_commits_formatted.append(f"• {subject} ({author}, {date})")
                    local_commit_links.append(f"- [{short_hash}]({repo_url}/commit/{full_hash}) {subject} - {author}")
                else:
                    local_commits_formatted.append(f"• {line}")
                    local_commit_links.append(f"- {line}")
            else:
                local_commits_formatted.append(f"• {line}")
                local_commit_links.append(f"- {line}")
        
        # Progress indicator for very large sets
        if len(lines) > 200 and i % (chunk_size * 4) == 0:
            print(f"📊 Processed {min(i + chunk_size, len(lines))}/{len(lines)} commits...")
    
    return local_commits_formatted, local_commit_links

def cleanup_temp_files():
    """Clean up temporary files to free memory"""
    temp_files = ['commits.txt', 'commits_extended.txt', 'files_changed.txt', 'lines_added.tmp', 'lines_deleted.tmp']
    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except:
            pass

@retry_api_call(max_retries=3, delay=2, timeout=30)
def merge_chunk_summaries(chunk_summaries, summary_type, total_commits, num_chunks):
    """Merge multiple chunk summaries into a single cohesive summary"""
    print(f"🔄 Merging {num_chunks} {summary_type} chunk summaries...")

    combined_chunks = "\n\n---\n\n".join([f"Chunk {i+1}:\n{summary}" for i, summary in enumerate(chunk_summaries)])

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

Use the same structure and formatting as the individual chunks.
Language: {output_language}

Generate the merged {summary_type}:
""").strip()

    # Check prompt size and truncate if needed (safety net for 413 errors)
    MAX_MERGE_PROMPT_CHARS = 100000  # ~25K tokens, safe limit for most models
    if len(merge_prompt) > MAX_MERGE_PROMPT_CHARS:
        print(f"⚠️  Merge prompt too large ({len(merge_prompt)} chars), truncating to {MAX_MERGE_PROMPT_CHARS}")
        merge_prompt = merge_prompt[:MAX_MERGE_PROMPT_CHARS] + "\n\n[Some chunk summaries truncated due to size limits]"

    # Validate request size before sending (fail fast with clear error)
    estimated_tokens = len(merge_prompt) // 4
    if estimated_tokens > 120000:  # Most models have 128K context limit
        raise ValueError(f"Merge prompt too large (~{estimated_tokens} tokens). Consider using smaller batch_size in hierarchical merge.")

    if estimated_tokens > 30000:
        print(f"⚠️  Warning: Large merge payload (~{estimated_tokens} tokens)")

    # Use higher token limit for merging
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert technical writer who creates comprehensive, well-organized summaries."},
            {"role": "user", "content": merge_prompt}
        ],
        max_tokens=6000,  # Higher limit for merged output
        temperature=0.3,
        extra_headers={
            "HTTP-Referer": f"https://github.com/{os.getenv('GITHUB_REPOSITORY', 'unknown')}",
            "X-Title": "Weekly-Changelog-Generator"
        }
    )

    merged_summary = response.choices[0].message.content.strip()

    if not merged_summary or len(merged_summary) < 50:
        raise ValueError(f"Merged {summary_type} too short or empty")

    return merged_summary

def hierarchical_merge_summaries(chunk_summaries, summary_type, total_commits, batch_size=5):
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
            return merge_chunk_summaries(chunk_summaries, summary_type, total_commits, num_summaries)
        except Exception as e:
            if "413" in str(e) or "too large" in str(e).lower():
                # Reduce batch size and retry
                if batch_size > 2:
                    print(f"⚠️ Payload too large with batch_size={batch_size}, reducing to {batch_size - 1}")
                    return hierarchical_merge_summaries(chunk_summaries, summary_type, total_commits, batch_size - 1)
            raise

    # Merge in batches
    print(f"🔄 Hierarchical merge: {num_summaries} summaries in batches of {batch_size}")
    merged_batches = []

    for i in range(0, num_summaries, batch_size):
        batch = chunk_summaries[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (num_summaries + batch_size - 1) // batch_size
        print(f"  📦 Merging batch {batch_num}/{total_batches} ({len(batch)} summaries)")

        try:
            merged = merge_chunk_summaries(batch, summary_type, total_commits, len(batch))
            merged_batches.append(merged)
        except Exception as e:
            if "413" in str(e) or "too large" in str(e).lower():
                # Try with smaller batch
                print(f"  ⚠️ Batch too large, splitting further")
                for sub_batch in [batch[:len(batch)//2], batch[len(batch)//2:]]:
                    if sub_batch:
                        sub_merged = hierarchical_merge_summaries(sub_batch, summary_type, total_commits, max(2, batch_size - 2))
                        merged_batches.append(sub_merged)
            else:
                raise

    # Recursively merge the merged batches
    return hierarchical_merge_summaries(merged_batches, summary_type, total_commits, batch_size)

# Process commits with chunking for large sets
commits_formatted, commit_links = process_commits_in_chunks(commits_raw)
total_commits = len(commits_formatted)

# Commit count validation and diagnostics
days_back = os.getenv("DAYS_BACK", "7")
print(f"📊 Validation: Processing {total_commits} commits for {days_back}-day period")

# Warn if commit count seems unusually low
if total_commits > 0:
    expected_min_commits = int(days_back) // 7  # Very conservative estimate (1 commit per week)
    if total_commits < expected_min_commits:
        print(f"⚠️  Warning: Only found {total_commits} commits for {days_back} days - this may indicate:")
        print(f"   - Git fetch depth limitation (increase fetch-depth in workflow)")
        print(f"   - Actual low activity period")
        print(f"   - Git filters may be too aggressive")

# Intelligent chunking system for large commit sets
COMMITS_PER_CHUNK = 5  # Small chunks for highly detailed analysis
use_chunking = total_commits > COMMITS_PER_CHUNK
num_chunks = 0
chunks_info = ""

if use_chunking:
    num_chunks = (total_commits + COMMITS_PER_CHUNK - 1) // COMMITS_PER_CHUNK  # Ceiling division
    print(f"📊 Large commit set detected ({total_commits} commits)")
    print(f"🔄 Will analyze in {num_chunks} chunks of ~{COMMITS_PER_CHUNK} commits each for detailed analysis")
    print(f"💡 This approach ensures each commit gets focused attention before merging into comprehensive summary")
    chunks_info = f"\n\n> 📊 **Note**: This changelog was generated by analyzing {total_commits} commits across {num_chunks} detailed chunks for comprehensive, high-quality coverage."
else:
    print(f"✅ Processing all {total_commits} commits in a single analysis")

commits_links_text = '\n'.join(commit_links)

# Build base context for extended analysis (used in all chunks)
extended_context = ""
if extended_analysis and extended_data:
    extended_context = f"\n\nDetailed file changes and statistics are also available for deeper analysis."
    if file_changes_data:
        # Limit file changes data to prevent oversized prompts (413 errors)
        MAX_FILE_CHANGES_CHARS = 5000
        if len(file_changes_data) > MAX_FILE_CHANGES_CHARS:
            print(f"⚠️  File changes data truncated ({len(file_changes_data)} -> {MAX_FILE_CHANGES_CHARS} chars)")
            file_changes_data = file_changes_data[:MAX_FILE_CHANGES_CHARS] + "\n... (truncated)"
        extended_context += f"\n\nFile changes summary:\n{file_changes_data}"

# Technical prompt template with explicit markdown formatting
tech_prompt_template = textwrap.dedent(f"""
You are a senior software developer writing a technical changelog for a development team.

Analyze these commits and create a structured technical summary in {output_language}:

{{base_context}}

Use this exact format with markdown:

### Technical Changelog Summary
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
- [Important technical context about frameworks, libraries, or patterns used]

Requirements:
- Use markdown headers (#### for sections)
- Use bold text (**text:**) for category labels
- Use bullet lists (-) for all items
- Keep it concise but informative with appropriate technical terminology
- Provide specific details about what was changed and why
{" - Focus on the most significant changes and their technical implications based on file statistics" if extended_analysis else ""}

Write in a clear, structured format with proper markdown formatting.
""").strip()

# Business prompt template with explicit markdown formatting
business_prompt_template = textwrap.dedent(f"""
You are a product manager communicating updates to stakeholders and end users.

Translate these technical commits into business impact in {output_language}:

{{base_context}}

Use this exact format with markdown:

### Summary of Recent Updates
[Write 2-3 sentence overview for non-technical audience explaining what was accomplished this week]

#### User Experience Impact
- [How these changes affect what users see and experience]
- [Specific improvements to interface or interactions]

#### Business Benefits
- [Value delivered to the organization]
- [How these changes support business goals]

#### Performance & Reliability
- [Improvements in system speed or responsiveness]
- [Enhanced stability or security]
- [Reduced errors or issues]

#### New Capabilities
- [New features or functionality now available]
- [What users can now do that they couldn't before]

#### Important Changes to Note
- [Breaking changes or significant updates users should be aware of]
- [Migration steps or actions needed, if any]

Requirements:
- Use markdown headers (#### for sections)
- Use bullet lists (-) for all items
- Avoid technical jargon and implementation details
- Focus on benefits, outcomes, and user value
- Explain the "why" behind changes in business terms
- Make it accessible to non-technical stakeholders
{" - Consider the overall scope and significance based on the extent of changes" if extended_analysis else ""}

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
        print(f"⚠️  Prompt too large ({len(prompt)} chars), truncating to {MAX_PROMPT_CHARS}")
        # Keep the beginning (template + commits) and truncate extended data at the end
        prompt = prompt[:MAX_PROMPT_CHARS] + "\n\n[Extended data truncated due to size limits]"

    # Validate request size before sending (fail fast with clear error)
    estimated_tokens = len(prompt) // 4
    if estimated_tokens > 120000:  # Most models have 128K context limit
        raise ValueError(f"Prompt too large (~{estimated_tokens} tokens). Consider reducing extended analysis data or days_back parameter.")

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
            {"role": "system", "content": "You are an experienced technical writer who creates clear, structured summaries with proper markdown formatting."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.3,
        extra_headers={
            "HTTP-Referer": f"https://github.com/{os.getenv('GITHUB_REPOSITORY', 'unknown')}",
            "X-Title": "Weekly-Changelog-Generator"
        }
    )

    # Validate response
    response_content = response.choices[0].message.content.strip()

    if not response_content or len(response_content) < 50:
        raise ValueError(f"AI response too short or empty for {description}")

    # Validate has markdown formatting
    if "###" not in response_content and "**" not in response_content:
        print(f"⚠️  Warning: {description} may be poorly formatted (missing markdown headers)")

    return response_content

def generate_chunked_summary(commits_list, prompt_template, description, summary_type):
    """Generate summary by processing commits in chunks and merging results"""
    if not use_chunking:
        # No chunking needed, process all commits at once
        commits_text = '\n'.join(commits_list)
        base_context = f"Commits:\n{commits_text}{extended_context}"
        prompt = prompt_template.format(base_context=base_context)
        return generate_summary(prompt, description)

    # Process in chunks
    chunk_summaries = []
    for chunk_idx in range(num_chunks):
        start_idx = chunk_idx * COMMITS_PER_CHUNK
        end_idx = min(start_idx + COMMITS_PER_CHUNK, total_commits)
        chunk_commits = commits_list[start_idx:end_idx]

        commits_text = '\n'.join(chunk_commits)
        base_context = f"Commits (chunk {chunk_idx + 1} of {num_chunks}, commits {start_idx + 1}-{end_idx}):\n{commits_text}{extended_context}"

        prompt = prompt_template.format(base_context=base_context)

        try:
            chunk_summary = generate_summary(prompt, description, chunk_number=chunk_idx + 1)
            chunk_summaries.append(chunk_summary)
            print(f"✅ Chunk {chunk_idx + 1}/{num_chunks} {description} completed")
        except Exception as e:
            print(f"⚠️  Warning: Failed to generate {description} for chunk {chunk_idx + 1}: {e}")
            # Continue with other chunks even if one fails
            chunk_summaries.append(f"[Chunk {chunk_idx + 1} analysis failed - commits {start_idx + 1}-{end_idx} not included in detail]")

    # Merge all chunk summaries
    if len(chunk_summaries) == 1:
        return chunk_summaries[0]
    elif len(chunk_summaries) > 1:
        return hierarchical_merge_summaries(chunk_summaries, summary_type, total_commits)
    else:
        raise Exception(f"No {description} chunks were successfully generated")

# Generate summaries with intelligent chunking and fallback
try:
    tech_summary = generate_chunked_summary(commits_formatted, tech_prompt_template, "technical summary", "technical")
    print("✅ Technical summary generated successfully")
except Exception as e:
    print(f"⚠️  Using fallback for technical summary due to: {str(e)}")
    tech_summary = config['fallback_tech']

try:
    business_summary = generate_chunked_summary(commits_formatted, business_prompt_template, "business summary", "business")
    print("✅ Business summary generated successfully")
except Exception as e:
    print(f"⚠️  Using fallback for business summary due to: {str(e)}")
    business_summary = config['fallback_business']

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
    "Spanish": "%d/%m/%Y"
}
date_format = date_formats.get(output_language, "%m-%d-%Y")
formatted_date = today.strftime(date_format)

# Check for duplicate entries and handle force mode
changelog_path = "CHANGELOG.md"
week_header = f"## {config['week_label']} {week_num}, {year}"
force_suffix = f" {config['force_updated']}" if force_update else ""

try:
    if os.path.exists(changelog_path):
        with open(changelog_path, "r", encoding="utf-8") as f:
            existing_content = f.read()
        
        if week_header in existing_content and not force_update:
            print(f"⚠️  Entry for {config['week_label']} {week_num}, {year} already exists. Use force=true to update anyway.")
            sys.exit(0)
        elif week_header in existing_content and force_update:
            print(f"🔧 Force mode: Updating existing entry for {config['week_label']} {week_num}, {year}")
            # Remove existing entry
            lines = existing_content.split('\n')
            new_lines = []
            skip_section = False
            
            for line in lines:
                if line.startswith(week_header):
                    skip_section = True
                    continue
                elif line.startswith('## ') and skip_section:
                    skip_section = False
                    new_lines.append(line)
                elif line.startswith('---') and skip_section:
                    skip_section = False
                    continue
                elif not skip_section:
                    new_lines.append(line)
            
            existing_content = '\n'.join(new_lines)
    else:
        existing_content = f"# {config['changelog_title']}\n\n{config['auto_updated']}\n"

    # Prepare statistics section for extended analysis
    stats_section = ""
    if extended_analysis:
        lines_added = os.getenv("LINES_ADDED", "0")
        lines_deleted = os.getenv("LINES_DELETED", "0")
        files_changed = os.getenv("FILES_CHANGED", "0")
        
        stats_section = f"""
### {config['statistics']}
- **{lines_added}** {config['lines_added']}
- **{lines_deleted}** {config['lines_deleted']} 
- **{files_changed}** {config['files_changed']}
"""
        
        if file_changes_data:
            stats_section += f"""
### {config['file_changes']}
{file_changes_data}
"""

    # Create changelog entry with chunking info if applicable
    changelog_entry = textwrap.dedent(f"""
{week_header}{force_suffix}

*{config['generated_on']} {formatted_date} - {len(commits_formatted)} {config['commits_label']}*
{chunks_info}

### {config['tech_changes']}
{tech_summary}

### {config['user_impact']}
{business_summary}
{stats_section}
### {config['all_commits']}
{commits_links_text}

---
""").strip()

    # Prepend new entry to the changelog (after header)
    lines = existing_content.split('\n')
    header_end = 0
    
    # Find where to insert (after the main header and description)
    for i, line in enumerate(lines):
        if line.startswith('# ') or line.strip() == config['auto_updated']:
            header_end = i + 1
        elif line.startswith('## ') or (i > 0 and lines[i-1].strip() == config['auto_updated']):
            break
    
    # Insert the new entry
    new_lines = lines[:header_end] + ['', changelog_entry, ''] + lines[header_end:]
    new_content = '\n'.join(new_lines)

    # Write updated changelog
    with open(changelog_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    action = "updated (forced)" if force_update else "updated"
    print(f"✅ Changelog {action} for {config['week_label']} {week_num}, {year}")

except Exception as e:
    print(f"❌ Error writing changelog: {str(e)}")
    print(f"💡 Common causes:")
    print(f"   - File permissions issue")
    print(f"   - Disk space issue")
    print(f"   - Invalid markdown content")
    cleanup_temp_files()
    sys.exit(1)

finally:
    # Clean up temporary files
    cleanup_temp_files()
    print("🧹 Cleaned up temporary files")
