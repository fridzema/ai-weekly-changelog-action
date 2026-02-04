[![CI](https://github.com/fridzema/ai-weekly-changelog-action/actions/workflows/ci.yml/badge.svg)](https://github.com/fridzema/ai-weekly-changelog-action/actions/workflows/ci.yml)

# Weekly Changelog Action

This GitHub Action automatically generates a weekly changelog from your repository's recent commits using an AI model via [OpenRouter](https://openrouter.ai). It summarizes technical changes and their business impact, then commits the update to a `CHANGELOG.md` file.

## Features

-   **AI-Powered Summaries:** Generates separate technical and user-facing summaries.
-   **Multi-Language Support:** Outputs changelogs in English, Dutch, German, French, or Spanish.
-   **Customizable:** Control the look-back period, AI model, and more.
-   **Extended Analysis:** Optionally perform a deeper analysis of file changes and statistics.
-   **Automatic Commits:** Commits the updated `CHANGELOG.md` file back to your repository.

## Usage

Create a workflow file in the repository where you want to generate the changelog (e.g., `.github/workflows/changelog.yml`).

### Example Workflow

This workflow runs every Monday at 06:00 UTC and can also be triggered manually.

```yaml
# .github/workflows/changelog.yml
name: Weekly Changelog

on:
  schedule:
    - cron: '0 6 * * MON' # Every Monday at 06:00 UTC
  workflow_dispatch:
    inputs:
      force:
        description: 'Force update even if week entry already exists'
        type: boolean
        default: false

jobs:
  create_changelog:
    runs-on: ubuntu-latest
    
    # IMPORTANT: This permission is required to commit the changelog file
    permissions:
      contents: write 

    steps:
      - name: Generate Weekly Changelog
        uses: your-github-username/your-action-repo-name@v1 # <-- IMPORTANT: Change this
        with:
          # Required: Your OpenRouter API key
          openrouter_api_key: ${{ secrets.OPENROUTER_API_KEY }}

          # Optional inputs with their defaults:
          # days_back: 7
          # model: 'openai/gpt-5-mini'
          # language: 'English'
          # extended: false
          force: ${{ github.event.inputs.force || false }}
```

### Testing Configuration (Dry Run)

To test your configuration without committing changes to the repository:

```yaml
# .github/workflows/test-changelog.yml
name: Test Changelog Generation

on:
  workflow_dispatch:

jobs:
  test_changelog:
    runs-on: ubuntu-latest
    permissions:
      contents: read  # Only read permission needed for dry run

    steps:
      - name: Test Changelog Generation
        uses: your-github-username/your-action-repo-name@v1
        with:
          openrouter_api_key: ${{ secrets.OPENROUTER_API_KEY }}
          dry_run: true  # Generate changelog without committing
          days_back: 7
          language: 'English'
```

When `dry_run` is enabled:
- The changelog is generated normally using AI
- The output is displayed in the GitHub Actions step summary (first 100 lines)
- No commit is made to the repository
- Perfect for testing configuration changes or different models

## Using This Action in Your Repository

📄 **Quick Start**: Copy one of these example files to your repository:
- [Simple Example](.github/workflows/example-simple.yml) - Automatic weekly runs only
- [Full Example](.github/workflows/example-full.yml) - All parameters with manual controls

### Simple Usage (Scheduled Weekly)

Create a workflow file in your repository at `.github/workflows/changelog.yml`:

```yaml
name: Generate Weekly Changelog

on:
  schedule:
    - cron: '0 6 * * MON' # Every Monday at 06:00 UTC
  workflow_dispatch: # Allows manual trigger

jobs:
  changelog:
    runs-on: ubuntu-latest
    permissions:
      contents: write # Required for committing the changelog

    steps:
      - name: Generate Weekly Changelog
        uses: fridzema/ai-weekly-changelog-action@main  # or @v1, @latest
        with:
          openrouter_api_key: ${{ secrets.OPENROUTER_API_KEY }}
          # Optional: customize behavior
          # days_back: 7
          # model: 'openai/gpt-5-mini'
          # language: 'English'
          # extended: false
          # force: false
```

**Important Notes**:
- ✅ **DO NOT** add a separate checkout step - the action handles this internally
- ✅ **DO NOT** pass `github_token` - the action uses it automatically from GitHub context
- ✅ **DO** set `permissions: contents: write` in your job
- ✅ **DO** add your OpenRouter API key to repository secrets

### Advanced Usage (Full Manual Control with All Parameters)

Complete example with all available parameters exposed for manual testing:

```yaml
name: Generate Weekly Changelog

on:
  schedule:
    - cron: '0 6 * * MON' # Every Monday at 06:00 UTC
  workflow_dispatch:
    inputs:
      days_back:
        description: 'Number of days to look back for commits (1-365)'
        type: choice
        required: false
        default: '7'
        options:
          - '1'
          - '7'
          - '14'
          - '30'
          - '60'
          - '90'
      model:
        description: 'OpenRouter AI model to use'
        type: choice
        required: false
        default: 'openai/gpt-5-mini'
        options:
          - 'openai/gpt-5-mini'
          - 'openai/gpt-4o-mini'
          - 'anthropic/claude-3-haiku'
          - 'anthropic/claude-3-5-sonnet'
          - 'google/gemini-flash-1.5'
      language:
        description: 'Output language for the changelog'
        type: choice
        required: false
        default: 'English'
        options:
          - 'English'
          - 'Dutch'
          - 'German'
          - 'French'
          - 'Spanish'
      extended:
        description: 'Enable extended analysis (file changes, statistics)'
        type: boolean
        required: false
        default: false
      force:
        description: 'Force update existing week entry'
        type: boolean
        required: false
        default: false
      dry_run:
        description: 'Preview without committing (test mode)'
        type: boolean
        required: false
        default: false

jobs:
  changelog:
    runs-on: ubuntu-latest
    permissions:
      contents: write # Required for committing changelog
      # Note: For dry_run only, you can use: contents: read

    steps:
      - name: Generate Weekly Changelog
        uses: fridzema/ai-weekly-changelog-action@main
        with:
          # Required
          openrouter_api_key: ${{ secrets.OPENROUTER_API_KEY }}

          # Optional - All parameters with fallbacks
          days_back: ${{ inputs.days_back || '7' }}
          model: ${{ inputs.model || 'openai/gpt-5-mini' }}
          language: ${{ inputs.language || 'English' }}
          extended: ${{ inputs.extended || false }}
          force: ${{ inputs.force || false }}
          dry_run: ${{ inputs.dry_run || false }}
```

**How to use**:
1. Copy this file to `.github/workflows/changelog.yml` in your repository
2. Add `OPENROUTER_API_KEY` to your repository secrets
3. Go to **Actions** tab → **Generate Weekly Changelog** → **Run workflow**
4. Select your desired options from the dropdowns
5. Click **Run workflow**

**Testing workflow**:
- Start with `dry_run: true` to preview without committing
- Try different models to see which produces better output
- Use `extended: true` for detailed statistics and file changes
- Use `force: true` to regenerate an existing week's entry

💡 **Pro tip**: See [.github/workflows/example-full.yml](.github/workflows/example-full.yml) for a fully documented, copy-paste ready example with all parameters and detailed comments.

### Common Mistakes to Avoid

❌ **Don't do this** (redundant checkout):
```yaml
steps:
  - uses: actions/checkout@v4  # ← NOT NEEDED - Action does this internally
  - uses: fridzema/ai-weekly-changelog-action@main
    with:
      openrouter_api_key: ${{ secrets.OPENROUTER_API_KEY }}
```

❌ **Don't pass github_token** (deprecated, causes warnings):
```yaml
- uses: fridzema/ai-weekly-changelog-action@main
  with:
    openrouter_api_key: ${{ secrets.OPENROUTER_API_KEY }}
    github_token: ${{ secrets.GITHUB_TOKEN }}  # ← NOT NEEDED - Causes warnings
```

✅ **Do this** (clean and simple):
```yaml
steps:
  - uses: fridzema/ai-weekly-changelog-action@main
    with:
      openrouter_api_key: ${{ secrets.OPENROUTER_API_KEY }}
```

### Testing Your Setup

1. **Dry Run First** (recommended):
   ```yaml
   - uses: fridzema/ai-weekly-changelog-action@main
     with:
       openrouter_api_key: ${{ secrets.OPENROUTER_API_KEY }}
       dry_run: true  # Preview without committing
   ```

2. **Check the workflow summary** - dry run output appears in the GitHub Actions step summary

3. **Run for real** - remove `dry_run: true` to commit the changelog

### Version Pinning

For production use, pin to a specific version instead of `@main`:

```yaml
uses: fridzema/ai-weekly-changelog-action@v1.0.0  # Pin to specific release
# or
uses: fridzema/ai-weekly-changelog-action@v1      # Pin to major version
```

Check the [releases page](https://github.com/fridzema/ai-weekly-changelog-action/releases) for available versions.

### Prerequisites

1.  **Add OpenRouter API Key to Secrets:**
    *   In your repository, go to `Settings` > `Secrets and variables` > `Actions`.
    *   Click `New repository secret`.
    *   Name the secret `OPENROUTER_API_KEY`.
    *   Paste your OpenRouter API key as the value.

## Action Inputs

| Input                | Description                                                                  | Required | Default                    |
| -------------------- | ---------------------------------------------------------------------------- | -------- | -------------------------- |
| `openrouter_api_key` | API key for OpenRouter.ai.                                                   | `true`   | `N/A`                      |
| `github_token`       | GitHub token for checking out code and committing changes.                   | `true`   | `${{ github.token }}`      |
| `days_back`          | Number of days to look back for commits (1-365).                             | `false`  | `7`                        |
| `model`              | The OpenRouter model to use (e.g., `openai/gpt-5-mini`).                    | `false`  | `openai/gpt-5-mini`       |
| `language`           | Output language. Options: `English`, `Dutch`, `German`, `French`, `Spanish`. | `false`  | `English`                  |
| `force`              | Force update even if an entry for the current week already exists.           | `false`  | `false`                    |
| `extended`           | Enable extended analysis with file changes and deeper commit inspection.     | `false`  | `false`                    |
| `dry_run`            | Generate changelog without committing (outputs to step summary instead).     | `false`  | `false`                    |