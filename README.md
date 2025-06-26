# Weekly Changelog via OpenRouter

This is a reusable workflow to generate a weekly changelog using OpenRouter and OpenAI.

## Usage

```yaml
name: Weekly Changelog

on:
  workflow_dispatch:

jobs:
  changelog:
    uses: your-org/weekly-changelog-action/.github/workflows/ai-changelog.yml@main
    with:
      days_back: 7
      language: English
      # ...other inputs
    secrets:
      OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}