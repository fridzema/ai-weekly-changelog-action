import os
import sys
import datetime
import textwrap
import time
import re
from functools import wraps
from openai import OpenAI
import json

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
                        print(f"💡 The model '{os.getenv('MODEL', 'openai/gpt-4o-mini')}' may not be available.")
                        print(f"💡 Check available models at: https://openrouter.ai/models")
                        print(f"💡 Consider using 'openai/gpt-4o-mini' or 'anthropic/claude-3-haiku' as alternatives.")
                        raise Exception(f"Model availability error: {str(e)}")
                    
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

model = os.getenv("MODEL", "openai/gpt-4o-mini")
output_language = os.getenv("OUTPUT_LANGUAGE", "English")
force_update = os.getenv("FORCE_UPDATE", "false").lower() == "true"
extended_analysis = os.getenv("EXTENDED_ANALYSIS", "false").lower() == "true"

print(f"🤖 Using model: {model}")
print(f"🌍 Output language: {output_language}")
print(f"🔧 Force update: {force_update}")
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
                    file_changes_summary.append(f"**{group}**: {', '.join(files[:5])}")
                    if len(files) > 5:
                        file_changes_summary.append(f"  _(and {len(files)-5} more)_")
                
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

# Process commits with chunking for large sets  
commits_formatted, commit_links = process_commits_in_chunks(commits_raw)
total_commits = len(commits_formatted)

# Handle large commit sets by summarizing in chunks
MAX_COMMITS_PER_ANALYSIS = 100  # Reasonable limit for AI processing
if total_commits > MAX_COMMITS_PER_ANALYSIS:
    print(f"📊 Large commit set detected ({total_commits} commits). Using streaming approach...")
    
    # Take most recent commits for detailed analysis
    recent_commits = commits_formatted[:MAX_COMMITS_PER_ANALYSIS]
    recent_text = '\n'.join(recent_commits)
    
    # Create summary of remaining commits
    remaining_count = total_commits - MAX_COMMITS_PER_ANALYSIS
    summary_text = f"\n\n[Additional {remaining_count} commits not shown in detail - included in statistics]"
    
    commits_text = recent_text + summary_text
    print(f"🔍 Analyzing most recent {MAX_COMMITS_PER_ANALYSIS} commits in detail, {remaining_count} additional commits included in stats")
else:
    commits_text = '\n'.join(commits_formatted)

commits_links_text = '\n'.join(commit_links)

# Enhanced prompts with extended data
base_context = f"Commits:\n{commits_text}"

if extended_analysis and extended_data:
    base_context += f"\n\nDetailed file changes and statistics are also available for deeper analysis."
    if file_changes_data:
        base_context += f"\n\nFile changes summary:\n{file_changes_data}"

# Detailed prompts for richer analysis
tech_extended = ', 4) Impact assessment based on file changes and statistics' if extended_analysis else ''
business_extended = ', 4) Overall scope and significance of this week\'s changes' if extended_analysis else ''
tech_note = ' Focus on the most significant changes and their technical implications.' if extended_analysis else ''
business_note = ' Consider the scope of changes when assessing business impact.' if extended_analysis else ''

# Enhanced technical prompt for detailed analysis
tech_prompt = textwrap.dedent(f"""
You are a senior software developer writing a technical changelog for a development team.

Analyze these commits and create a comprehensive technical summary:

{base_context}

Please provide a detailed technical summary in {output_language} that includes:

1. **Brief Introduction** (1-2 sentences): Overview of the week's development activity
2. **Main Changes by Category**: 
   - **Features**: New functionality added
   - **Bug Fixes**: Issues resolved and fixes implemented
   - **Refactoring**: Code improvements, cleanup, and restructuring
   - **Infrastructure/DevOps**: Build, deployment, and tooling changes
   - **Documentation**: Updates to docs and comments
   - **Testing**: Test additions and improvements
3. **Technical Highlights**: Key architectural decisions, performance improvements, security enhancements
{tech_extended and "4. **Impact Assessment**: Based on file changes and statistics, assess the scope and significance of changes" or ""}

Requirements:
- Use appropriate technical terminology for developers
- Provide specific details about what was changed and why
- Mention important technical decisions and their rationale
- Include relevant technical context (frameworks, libraries, patterns used)
- Keep it comprehensive but well-organized
{tech_note}

Write in a clear, technical style suitable for software developers.
""").strip()

# Enhanced business prompt for stakeholder communication
business_prompt = textwrap.dedent(f"""
You are a product manager communicating technical updates to stakeholders, end users, and business leaders.

Analyze these technical commits and translate them into business impact:

{base_context}

Write a comprehensive business summary in {output_language} that non-technical people can understand:

1. **User Experience Impact**: How do these changes affect what users see and experience?
2. **Business Benefits**: What value do these changes bring to the organization?
3. **Performance & Reliability**: Improvements in system performance, stability, or security
4. **New Capabilities**: What new features or functionality are now available?
5. **Risk Mitigation**: What problems were solved or prevented?
{business_extended and "6. **Overall Scope**: Based on the extent of changes, assess the significance of this week's development" or ""}

Requirements:
- Avoid technical jargon and implementation details
- Focus on benefits, outcomes, and user value
- Explain the "why" behind changes in business terms
- Highlight improvements to user experience, performance, or capabilities
- Make it accessible to non-technical stakeholders
{business_note}

Write in a clear, business-focused style suitable for stakeholders and end users.
""").strip()

# Combined prompt that generates both summaries in one call for consistency
combined_prompt = textwrap.dedent(f"""
You are an experienced technical writer creating a comprehensive weekly changelog. Analyze these commits and provide both technical and business perspectives.

{base_context}

Generate detailed summaries for both technical and business audiences. Respond with a JSON object containing exactly two fields:

{{
  "technical_summary": "A comprehensive technical summary in {output_language} for developers, including: 1) Brief introduction, 2) Main changes by category (Features, Bugfixes, Refactoring, Infrastructure, etc.), 3) Technical highlights and architectural decisions{tech_extended}",
  "business_summary": "A comprehensive business summary in {output_language} for stakeholders and end users, including: 1) User experience impact, 2) Business benefits and value, 3) Performance and reliability improvements, 4) New capabilities, 5) Risk mitigation{business_extended}"
}}

Technical Summary Requirements:
- Use appropriate technical terminology for developers
- Provide specific details about what was changed and why
- Mention important technical decisions and their rationale
- Include relevant technical context (frameworks, libraries, patterns used)
- Organize by categories: Features, Bug Fixes, Refactoring, Infrastructure, Documentation, Testing
- Keep it comprehensive but well-organized
{tech_note}

Business Summary Requirements:
- Avoid technical jargon and implementation details
- Focus on benefits, outcomes, and user value
- Explain the "why" behind changes in business terms
- Highlight improvements to user experience, performance, or capabilities
- Make it accessible to non-technical stakeholders
{business_note}

Respond only with valid JSON. Make both summaries detailed and informative.
""").strip()

@retry_api_call(max_retries=3, delay=2, timeout=30)
def generate_combined_summary(prompt, commit_count, is_large_set=False):
    print(f"🔄 Generating combined technical and business summaries...")
    
    # Enhanced token calculation for detailed analysis
    base_tokens = 1200  # Increased base for detailed prompts
    tokens_per_commit = 35  # Slightly more per commit for detailed analysis
    extended_bonus = 600 if extended_analysis else 0  # More for extended analysis
    large_set_bonus = 300 if is_large_set else 0  # Extra tokens for large set context
    
    # Cap the commit-based calculation for very large sets
    effective_commit_count = min(commit_count, MAX_COMMITS_PER_ANALYSIS)
    max_tokens = min(3500, base_tokens + (effective_commit_count * tokens_per_commit) + extended_bonus + large_set_bonus)
    
    if is_large_set:
        print(f"📝 Using enhanced token allocation ({max_tokens}) for large commit set processing")
    
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an experienced technical writer who creates clear, structured summaries. Always respond with valid JSON."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=max_tokens,
        temperature=0.3,
        extra_headers={
            "HTTP-Referer": f"https://github.com/{os.getenv('GITHUB_REPOSITORY', 'unknown')}",
            "X-Title": "Weekly-Changelog-Generator"
        }
    )
    return response.choices[0].message.content.strip()

# Generate combined summaries with fallback
try:
    is_large_commit_set = total_commits > MAX_COMMITS_PER_ANALYSIS
    combined_response = generate_combined_summary(combined_prompt, total_commits, is_large_commit_set)
    print("✅ Combined summaries generated successfully")
    
    # Parse JSON response
    try:
        summaries = json.loads(combined_response)
        tech_summary = summaries.get('technical_summary', config['fallback_tech'])
        business_summary = summaries.get('business_summary', config['fallback_business'])
    except json.JSONDecodeError as e:
        print(f"⚠️  Failed to parse JSON response: {str(e)}")
        print(f"Raw response: {combined_response[:200]}...")
        tech_summary = config['fallback_tech']
        business_summary = config['fallback_business']
        
except Exception as e:
    print(f"⚠️  Using fallback summaries due to: {str(e)}")
    tech_summary = config['fallback_tech']
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

    # Create changelog entry
    changelog_entry = textwrap.dedent(f"""
{week_header}{force_suffix}

*{config['generated_on']} {formatted_date} - {len(commits_formatted)} {config['commits_label']}*

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
