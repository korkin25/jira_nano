# Security Policy

## Reporting a vulnerability

Please report suspected vulnerabilities **privately** — do not open a public issue.

- Preferred: GitHub **private vulnerability reporting** (Security → *Report a vulnerability*).
- Or contact the maintainer (`korkin25`) privately.

Include a description, reproduction steps, affected versions, and impact. We aim to
acknowledge within a few business days.

## Handling secrets

No secrets are ever committed. The Telegram bot token, any session file, and API tokens
(`JIRA_NANO_TOKENS`) are loaded from the environment or ignored local files only, and are
treated as **full-access credentials** — the bot token grants full access to the bot's
identity. If you believe a secret was exposed, revoke/rotate it immediately and report it.

## Automated checks

CI runs a security suite on every push/PR: `gitleaks`, `bandit`, `pip-audit`, `semgrep`,
`checkov`, `hadolint`, `trivy`, and GitHub CodeQL. Dependency updates are proposed by
Dependabot. See [`CLAUDE.md`](CLAUDE.md) § *Build, artifacts & CI* and § *Agent security
working agreements*.
