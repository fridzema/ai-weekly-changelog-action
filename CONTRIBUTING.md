# Contributing to AI Weekly Changelog Action

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to this project.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How to Contribute

### Reporting Bugs

Before creating a bug report:
1. Check [existing issues](https://github.com/fridzema/ai-weekly-changelog-action/issues) to avoid duplicates
2. Use the bug report template when creating a new issue
3. Include:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Action version and configuration
   - Relevant logs (with secrets redacted)

### Suggesting Features

1. Check [existing issues](https://github.com/fridzema/ai-weekly-changelog-action/issues) for similar suggestions
2. Use the feature request template
3. Describe:
   - The problem you're trying to solve
   - Your proposed solution
   - Alternative approaches you've considered

### Pull Requests

1. Fork the repository
2. Create a feature branch from `main`
3. Make your changes
4. Ensure tests pass
5. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.10+
- Git
- An OpenRouter API key (for integration testing)

### Local Development

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ai-weekly-changelog-action.git
cd ai-weekly-changelog-action

# Install development dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -v

# Run linting
ruff check src/
black --check src/
```

### Testing the Action Locally

```bash
# Set required environment variables
export OPENROUTER_API_KEY="your-key-here"
export GITHUB_REPOSITORY="owner/repo-name"
export MODEL="openai/gpt-4o-mini"
export OUTPUT_LANGUAGE="English"
export DAYS_BACK="7"

# Create test commit data
git log --since="7 days ago" --no-merges \
    --pretty=format:'%H\x1f%s\x1f%an\x1f%ad\x1f%h' \
    --date=short > commits.txt

# Run the Python script
python src/generate_changelog.py
```

## Code Style

### Python

We use **ruff** for linting and **black** for formatting:

```bash
# Format code
black src/ tests/

# Check linting
ruff check src/ tests/

# Auto-fix linting issues
ruff check --fix src/ tests/
```

Configuration is in `pyproject.toml`:
- Line length: 100 characters
- Target Python: 3.11+

### YAML (action.yml, workflows)

- Use 2-space indentation
- Quote strings that could be interpreted as other types
- Include meaningful comments for complex logic

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, no code change
- `refactor`: Code change without feature/fix
- `test`: Adding or updating tests
- `chore`: Build process, dependencies

Examples:
```
feat(inputs): add commits_per_chunk parameter
fix(parsing): handle pipe characters in commit messages
docs(readme): add cost estimation table
```

## Testing

### Running Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific test file
pytest tests/test_parsing.py -v
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Use pytest fixtures for common setup
- Mock external API calls (never call real APIs in tests)

Example:
```python
def test_parse_commit_with_pipe_in_message():
    """Ensure pipe characters in commit messages don't break parsing."""
    raw = "abc123\x1fFix A|B comparison\x1fJohn\x1f2024-01-15\x1fabc"
    result = parse_commit_line(raw)
    assert result["subject"] == "Fix A|B comparison"
```

### CI Requirements

All PRs must pass:
- `ruff check` (linting)
- `black --check` (formatting)
- `pytest` (tests)
- `actionlint` (GitHub Actions syntax)
- `shellcheck` (shell scripts in workflows)

## Pull Request Process

1. **Create a branch**: `git checkout -b feat/my-feature`

2. **Make changes**: Follow code style guidelines

3. **Test locally**:
   ```bash
   pytest tests/ -v
   ruff check src/
   black --check src/
   ```

4. **Commit**: Use conventional commit messages

5. **Push**: `git push origin feat/my-feature`

6. **Open PR**: Use the PR template

7. **Address review feedback**: Make requested changes

8. **Merge**: Maintainers will merge once approved

### PR Checklist

- [ ] Tests added/updated for changes
- [ ] Documentation updated if needed
- [ ] Commit messages follow conventional commits
- [ ] All CI checks pass
- [ ] PR description explains the changes

## Release Process

Releases are managed by maintainers:

1. Changes merged to `main`
2. Version tag created (`v1.x.x`)
3. Release workflow triggers automatically
4. `v1` tag updated to point to latest release

## Questions?

- Check [SUPPORT.md](SUPPORT.md) for help resources
- Open a [discussion](https://github.com/fridzema/ai-weekly-changelog-action/discussions) for questions
- Review [existing issues](https://github.com/fridzema/ai-weekly-changelog-action/issues) for common problems

Thank you for contributing!
