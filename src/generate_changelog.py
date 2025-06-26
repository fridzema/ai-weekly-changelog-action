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
    """Decorator to retry API calls with exponential backoff and timeout"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        print(f"❌ Final attempt failed: {str(e)}")
                        raise
                    wait_time = delay * (2 ** attempt)
                    print(f"⚠️  API call failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    print(f"🔄 Retrying in {wait_time}s...")
                    time.sleep(wait_time)
            return None
        return wrapper
    return decorator

# Check if API key is present
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    print("❌ OPENROUTER_API_KEY not found in secrets")
    sys.exit(1)

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

# Format commits for better readability
commits_formatted = []
commit_links = []
repo_url = f"https://github.com/{os.getenv('GITHUB_REPOSITORY', 'unknown')}"

for line in commits_raw.split('\n'):
    if '|' in line:
        parts = line.split('|')
        if len(parts) >= 5:
            full_hash, subject, author, date, short_hash = parts[:5]
            commits_formatted.append(f"• {subject} ({author}, {date})")
            commit_links.append(f"- [{short_hash}]({repo_url}/commit/{full_hash}) {subject} - {author}")
        else:
            commits_formatted.append(f"• {line}")
            commit_links.append(f"- {line}")
    else:
        commits_formatted.append(f"• {line}")
        commit_links.append(f"- {line}")

commits_text = '\n'.join(commits_formatted)
commits_links_text = '\n'.join(commit_links)

# Enhanced prompts with extended data
base_context = f"Commits:\n{commits_text}"

if extended_analysis and extended_data:
    base_context += f"\n\nDetailed file changes and statistics are also available for deeper analysis."
    if file_changes_data:
        base_context += f"\n\nFile changes summary:\n{file_changes_data}"

# Combined prompt for both technical and business summaries
combined_prompt = textwrap.dedent(f"""
You are an experienced technical writer creating a weekly changelog. Analyze these commits and provide both technical and business perspectives.

{base_context}

Respond with a JSON object containing exactly two fields:

{{
  "technical_summary": "A technical summary in {output_language} for developers, including: 1) Brief introduction, 2) Main changes by category (Features, Bugfixes, Refactoring, etc.), 3) Technical highlights{', 4) Impact assessment based on file changes and statistics' if extended_analysis else ''}",
  "business_summary": "A business summary in {output_language} for stakeholders and end users, including: 1) What these changes mean for users, 2) What benefits they bring, 3) Important changes people should be aware of{', 4) Overall scope and significance of this week\'s changes' if extended_analysis else ''}"
}}

Technical summary: Use appropriate technical terminology. Keep concise but informative.{' Focus on the most significant changes and their technical implications.' if extended_analysis else ''}
Business summary: Avoid jargon and technical details. Focus on value and impact for end users.{' Consider the scope of changes when assessing business impact.' if extended_analysis else ''}

Respond only with valid JSON.
""").strip()

@retry_api_call(max_retries=3, delay=2, timeout=30)
def generate_combined_summary(prompt, commit_count):
    print(f"🔄 Generating combined technical and business summaries...")
    
    # Dynamic token calculation based on commit count and analysis type
    base_tokens = 800
    tokens_per_commit = 30
    extended_bonus = 400 if extended_analysis else 0
    max_tokens = min(2000, base_tokens + (commit_count * tokens_per_commit) + extended_bonus)
    
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
    combined_response = generate_combined_summary(combined_prompt, len(commits_formatted))
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
    sys.exit(1)
