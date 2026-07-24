# jira_nano

[![PyPI](https://img.shields.io/pypi/v/jira-nano)](https://pypi.org/project/jira-nano/)

A lightweight, **AI-native issue tracker** where the source of record is a Git
repository, the query layer is a rebuildable SQLite cache, and human
communication happens through a Telegram bot mirror instead of email.

> **Status: v0.3.2 — feature-complete, [on PyPI](https://pypi.org/project/jira-nano/).**
> All five phases are implemented (core git store + SQLite cache + CRUD, MCP
> server + HTTP Jira REST API, Telegram mirror, GitLab/GitHub integration, and
> skill/CLI packaging), with 211 tests, ruff + mypy clean, and CI. See
> [`CHANGELOG.md`](CHANGELOG.md).

## Install

```bash
pipx install "jira-nano[mcp,http,telegram]"   # surfaces are optional extras
```

Or straight from source (e.g. unreleased changes):
`pipx install "jira-nano[mcp,http,telegram] @ git+https://github.com/korkin25/jira_nano.git"`.

Then run the CLI (`jira-nano --help`) or the MCP server over stdio
(`jira-nano-mcp`). **Full hands-on setup** for every surface (MCP, HTTP API,
Telegram, GitLab/GitHub) is in
[`docs/install-guide.md`](docs/install-guide.md); release & publishing details
are in [`docs/packaging.md`](docs/packaging.md).

## Why

Traditional trackers hide state in a proprietary database and notify humans by
email. `jira_nano` inverts that:

- **State lives in Git**, so it is diffable, reviewable, versioned, and portable
  — the history *is* the audit trail.
- **AI agents are first-class users**, not an afterthought: an MCP server and an
  HTTP API expose the tracker with a tool shape close to common Jira MCP
  servers, so agent workflows are drop-in.
- **Notifications move to chat**, where people already are: a Telegram bot
  mirrors assignments, status, and updates, and pulls human replies back into
  the ticket files.

## Features

Highlights below; the full numbered list is in
[`Features.md`](Features.md).

- Git-backed ticket store: one Markdown file per ticket with YAML frontmatter.
- Rebuildable SQLite cache for fast search, filters, and boards.
- Telegram bot mirror: assignment `@mentions`, status icons, update posts, and
  comment pull-back.
- MCP server + HTTP API: `create` / `update` / `transition` / `assign` /
  `comment` / `search` / `list` / `board`.
- Git-host integration for **both GitLab and GitHub**: link commits and MRs/PRs
  to tickets, update status on events.
- Shipped as an Agent Skill (`SKILL.md`) for OpenClaw / Claude / other agents.
- Configurable, validated status workflow (draft — see
  [`docs/status-model.md`](docs/status-model.md)).

## How it works

```
              ┌──────────────────────────────────────────────┐
              │  Git repository  (SOURCE OF RECORD)           │
              │  tickets/JN-<n>.md  = YAML frontmatter + body  │
              └──────────────────────────────────────────────┘
                     │  rebuild ▲                │ read/write
                     ▼          │                │
              ┌───────────────┐ │        ┌───────┴────────────┐
              │ SQLite cache  │ │        │  MCP server + API   │◄── AI agents
              │ (derived)     │─┘        │  create/update/...  │◄── HTTP clients
              └───────────────┘          └───────┬────────────┘
                                                 │ mirror / pull-back
                                    ┌────────────┴───────────┐
                                    │  Telegram BOT mirror    │◄──► humans
                                    │  (forum topics/threads) │
                                    └─────────────────────────┘
              ┌──────────────────────────────────────────────┐
              │  Git-host integration (GitLab + GitHub)       │
              │  parse JN-<n> in commits / MR / PR → link+move │
              └──────────────────────────────────────────────┘
```

- **Git store** — tickets are versioned files; commits are the audit trail.
- **SQLite cache** — a rebuildable index; if deleted it is regenerated from the
  ticket files. Never authoritative.
- **Telegram mirror** — a **Bot API** bot (not a userbot) manages forum topics
  and posts to threads; it pings assignees, reflects status via icons, posts
  updates, and pulls user comments back into ticket files.
- **MCP / API** — one shared service layer validates transitions against the
  configured workflow and exposes the same operations to agents and HTTP
  clients.
- **Git-host integration** — webhooks (or polling) parse `JN-<n>` ids in commit
  messages and MR/PR titles for GitLab and GitHub, then link them and advance
  ticket status.

See [`docs/architecture.md`](docs/architecture.md) for the detailed design.

## Security

Secrets never live in Git. The Telegram bot token (and any Telethon session
file) is a **full-access credential** — keep it in the environment or in local
ignored files only, apply least privilege, and revoke on any suspected leak. The
SQLite cache is derived data and is also excluded from version control.

## License

[GPL-3.0-or-later](LICENSE).
