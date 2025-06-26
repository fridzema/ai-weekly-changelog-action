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
          # model: 'openai/gpt-4o-mini'
          # language: 'English'
          # extended: false
          force: ${{ github.event.inputs.force || false }}
```

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
| `model`              | The OpenRouter model to use (e.g., `openai/gpt-4o-mini`).                    | `false`  | `openai/gpt-4o-mini`       |
| `language`           | Output language. Options: `English`, `Dutch`, `German`, `French`, `Spanish`. | `false`  | `English`                  |
| `force`              | Force update even if an entry for the current week already exists.           | `false`  | `false`                    |
| `extended`           | Enable extended analysis with file changes and deeper commit inspection.     | `false`  | `false`                    |