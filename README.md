# Weekly Changelog via OpenRouter

This GitHub Action generates a weekly changelog by summarizing commits using OpenRouter's AI models. It provides both technical and business-friendly updates, and can be configured for extended analysis and different output languages.

## Usage

To use this action in your workflow, add a step like this:

```yaml
name: Generate Weekly Changelog

on:
  # You can trigger this workflow on a schedule, or manually
  workflow_dispatch:
  schedule:
    - cron: '0 0 * * 1' # Runs every Monday at 00:00 UTC

jobs:
  update_changelog:
    runs-on: ubuntu-latest
    permissions:
      contents: write # Required for committing changes to README.md

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0 # Fetch full git history for log commands
          token: ${{ secrets.GITHUB_TOKEN }} # Required for checkout and commit

      - name: Generate and Update Changelog
        uses: your-org/weekly-changelog-action@v1 # Replace 'your-org' with your GitHub username or organization name, and 'v1' with a tag or branch
        with:
          days_back: 7 # Optional: Number of days to look back for commits (default: 7)
          model: "openai/gpt-4o-mini" # Optional: OpenRouter model to use (default: openai/gpt-4o-mini)
          language: "English" # Optional: Output language for changelog (e.g., "English", "Dutch", "German", "French", "Spanish") (default: English)
          force: "false" # Optional: Force update even if week entry already exists ("true" or "false") (default: false)
          extended: "false" # Optional: Extended analysis with file changes and deeper commit inspection ("true" or "false") (default: false)
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }} # Required: Your OpenRouter API Key
