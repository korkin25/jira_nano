# Configuration — environment variables

Everything jira_nano needs at runtime is configured through environment variables.
Nothing sensitive is committed; secrets come from the environment (locally, from
Docker/compose or the Helm chart's `envFrom.secret`; in CI, from the GitHub
Actions environment — see [§ CI functional tests](#ci-functional-tests)).

## Core (HTTP Jira REST API — `jira-nano-http`)

| Variable | Default | Secret | Purpose |
|----------|---------|:------:|---------|
| `JIRA_NANO_REPO` | `.` | | Path to the git ticket store (the source of record). In the image: `/data/repo`. |
| `JIRA_NANO_HTTP_HOST` | `0.0.0.0` | | Bind host for the HTTP API. |
| `JIRA_NANO_HTTP_PORT` | `8080` | | Bind port for the HTTP API. |
| `JIRA_NANO_TOKENS` | `""` | ✅ | Bearer tokens, `user1:token1,user2:token2`. Empty ⇒ auth open. |
| `JIRA_NANO_OAUTH_CLIENTS` | `""` | ✅ | OAuth client-credentials, `client_id:client_secret,...`. |

## MCP server (`jira-nano-mcp-http` / `jira-nano-mcp`)

`jira-nano-mcp-http` serves the MCP over streamable-HTTP; `jira-nano-mcp` is stdio.
Both read `JIRA_NANO_REPO`. (Port/host are fixed by the MCP transport defaults.)

## Telegram mirror bot (`jira-nano-bot`)

| Variable | Default | Secret | Purpose |
|----------|---------|:------:|---------|
| `TELEGRAM_BOT_TOKEN` | — | ✅ | **Required.** Bot API token for the mirror. |
| `JIRA_NANO_MIRROR_INTERVAL` | `3.0` | | Change-feed poll interval (seconds). |

## Git-host webhooks (`jira-nano-webhooks`)

| Variable | Default | Secret | Purpose |
|----------|---------|:------:|---------|
| `JIRA_NANO_WEBHOOK_HOST` | `0.0.0.0` | | Bind host. |
| `JIRA_NANO_WEBHOOK_PORT` | `8081` | | Bind port. |
| `GITHUB_WEBHOOK_SECRET` | `""` | ✅ | HMAC secret for GitHub webhooks. |
| `GITLAB_WEBHOOK_SECRET` | `""` | ✅ | Token for GitLab webhooks. |

## Voice / STT (Telegram voice replies)

| Variable | Default | Secret | Purpose |
|----------|---------|:------:|---------|
| `JIRA_NANO_STT` | `auto` | | `auto` / `local` / `cloud`. `auto` uses cloud when `OPENAI_API_KEY` is set. |
| `JIRA_NANO_WHISPER_MODEL` | `base` | | Local faster-whisper model name. |
| `JIRA_NANO_STT_MODEL` | `whisper-1` | | Cloud (OpenAI) model name. |
| `OPENAI_API_KEY` | — | ✅ | Enables the cloud STT backend. |
| `HF_HOME` / `XDG_CACHE_HOME` | — | | Whisper model cache dir. In the chart: `/models` (the voice-model PVC). |

## Tests

| Variable | Default | Purpose |
|----------|---------|---------|
| `JIRA_NANO_LIVE` | unset | Set to `1` to enable the gated live/functional tests. |

## CI functional tests

The `functional` CI job reads a **minimal set** from the GitHub Actions
environment `ci-functional`:

- **Variable** `JIRA_NANO_TOKENS` — a throwaway CI-only bearer token used to hit
  the running API (non-secret; grants access only to the ephemeral in-CI instance).
- **Secrets** (optional; the Telegram-dependent checks are skipped when absent):
  `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`.

Set them with:

```bash
gh variable set JIRA_NANO_TOKENS --env ci-functional --body "ci:ci-functional-token"
gh secret   set TELEGRAM_BOT_TOKEN --env ci-functional   # paste the value when prompted
```
