# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| v1.x    | :white_check_mark: |
| < v1.0  | :x:                |

We recommend always using the latest `v1` tag for security updates.

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly:

1. **Do NOT open a public GitHub issue** for security vulnerabilities
2. **Use GitHub Security Advisories** (preferred): [Report a vulnerability](https://github.com/fridzema/ai-weekly-changelog-action/security/advisories/new)
3. Or contact via [GitHub Discussions](https://github.com/fridzema/ai-weekly-changelog-action/discussions) for non-critical security questions

### What to include

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 7 days
- **Resolution target**: Within 30 days for critical issues

## Privacy & Data Disclosure

### Data Sent to External Services

This action sends data to **OpenRouter's API** (and subsequently to the AI model provider you select). The following data is transmitted:

| Data Type | When Sent | Purpose |
|-----------|-----------|---------|
| Commit messages (subjects) | Always | Generate changelog summaries |
| Commit author names | Always | Attribution in summaries |
| Commit dates | Always | Temporal organization |
| Repository name | Always | Context for AI |
| File paths | Extended mode only | Detailed file change analysis |
| File change statistics | Extended mode only | Quantitative metrics |

### Data NOT Sent

- File contents (source code)
- Full commit diffs
- API keys or secrets (unless accidentally committed)
- Private repository metadata beyond commit info

### Recommendations for Sensitive Repositories

1. **Use `dry_run: true`** first to preview what will be generated
2. **Enable `redact_patterns`** to scrub sensitive patterns from commit messages
3. **Review commit messages** before running - they become AI input
4. **Consider organizational compliance** - check if sending commit data to third-party APIs is allowed

## API Key Security

### Best Practices

1. **Store API keys as GitHub Secrets** - never commit them to code
2. **Use organization-level secrets** when possible for easier rotation
3. **Enable secret scanning** on your repository
4. **Rotate keys periodically** and after any suspected exposure

### What We Do

- API keys are read from environment variables only
- Keys are never logged or included in outputs
- Keys are never committed to the changelog

### What You Should Do

```yaml
# Good: Use secrets
env:
  OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}

# Bad: Hardcoded keys (NEVER do this)
env:
  OPENROUTER_API_KEY: sk-or-v1-xxxxx  # NEVER!
```

## Prompt Injection Protection

This action includes protection against prompt injection attacks in commit messages:

- System prompts instruct the AI to treat commit messages as **data only**
- Commit messages are not interpreted as instructions
- Unusual patterns are not executed as commands

However, for maximum security:
- Review AI-generated content before publishing externally
- Consider commit message policies for your team
- Use `redact_patterns` to remove potentially sensitive patterns

## Third-Party Dependencies

| Dependency | Purpose | Security Considerations |
|------------|---------|------------------------|
| `openai` Python SDK | API communication | Well-maintained, security audited |
| OpenRouter API | AI model routing | Review their [security policy](https://openrouter.ai/docs) |

## Security Updates

- Watch this repository for security advisories
- Enable Dependabot alerts for dependency updates
- Subscribe to releases for security patches
