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

- **Git-backed ticket store** — one Markdown file per ticket (`tickets/JN-<n>.md`) with
  YAML frontmatter (`id`, `title`, `status`, `assignee`, `labels`, `priority`, dates,
  `links`) plus a Markdown body; Git history is the audit trail, and ids are sequential and
  never reused.
- **Rebuildable SQLite cache** — indexes ticket frontmatter for fast full-text and field
  search, filters (status/assignee/label/priority), and board views; regenerated from the
  ticket files at any time and never authoritative.
- **CRUD & search** — create, read, and update tickets through one shared service layer,
  with cache-backed search, filtered lists, and a board grouped by workflow status.
- **Configurable, validated workflow** — states and allowed transitions live in config;
  every mutating operation is validated against them; terminal states archive/close a
  ticket; status is mirrored to Telegram icons (see
  [`docs/status-model.md`](docs/status-model.md)).
- **MCP server + HTTP API** — `create` / `update` / `transition` / `assign` / `comment` /
  `search` / `list` / `board`, with a tool shape close to common Jira MCP servers, plus a
  drop-in Jira REST v2+v3 HTTP surface for non-MCP clients.
- **Telegram bot mirror** — a multi-user **Bot API** bot (not a userbot) manages a forum
  topic/thread per ticket, `@mention`s assignees, reflects status via icons, posts ticket
  updates, and pulls human comments written in Telegram back into the ticket files.
  Post-1.0 polish adds a message-design overhaul, a background auto-trigger, per-status
  banners, and voice-message transcription (pluggable STT — local Whisper by default,
  optional cloud).
- **Git-host integration (GitLab + GitHub)** — parse `JN-<n>` ids in commit messages and
  MR/PR titles across both hosts symmetrically, link commits and MRs/PRs into the ticket
  `links`, and advance ticket status on Git-host events (webhook-driven with polling
  fallback).
- **Agent Skill packaging** — shipped as an Agent Skill (`SKILL.md`) targeting the
  [Agent Skills](https://agentskills.io) standard, so agents (OpenClaw / Claude / others)
  manage tickets natively via the skill + MCP.

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
