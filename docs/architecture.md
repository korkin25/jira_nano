# Architecture

> Status: **planning / draft.** This document describes the intended design. No
> component is implemented yet.

`jira_nano` is built around one principle: **Git is the source of record, and
everything else is a derived projection or an integration surface.** Losing any
component other than the Git repository must be recoverable by rebuilding from
the ticket files.

## 1. Components

| Component | Role | Authoritative? |
|-----------|------|----------------|
| **Git ticket store** | Versioned ticket files under `tickets/` | **Yes** — source of record |
| **SQLite cache** | Rebuildable index for search/filter/board queries | No — derived |
| **Service / core layer** | Shared logic: CRUD, transition validation, indexing | No — stateless over the store |
| **MCP server** | Exposes tracker operations as MCP tools for agents | No |
| **HTTP API** | Same operations for HTTP clients | No |
| **Telegram bot mirror** | Communication mirror (pings, status icons, comment pull-back) | No — mirror only |
| **Git-host integration** | Links commits/MRs/PRs, moves status on events | No |
| **Agent Skill (`SKILL.md`)** | Packaging so agents can drive the tracker | No |

All read/write paths converge on the **service layer**, so validation (workflow
transitions, schema) happens in exactly one place regardless of whether the
caller is an agent (MCP), an HTTP client, the Telegram bot, or a Git-host event.

## 2. Storage model

### 2.1 Git ticket files (source of record)

One file per ticket: `tickets/JN-<n>.md`. YAML frontmatter carries structured
fields; the Markdown body carries the description and comment log.

```markdown
---
id: JN-123
type: task
title: Short human-readable summary
status: in-progress
priority: high
assignee: korkin25
reporter: eugeny
watchers: [eugeny, ivanov]
labels: [backend, telegram]
blocked: false
parent: JN-100
links:
  - {type: mr, host: gitlab, url: "https://gitlab.com/acme/proj/-/merge_requests/42", ref: "!42"}
created: 2026-07-24T09:00:00Z
updated: 2026-07-24T12:30:00Z
---

## Description

Free-form Markdown body.

## Comments

<!-- c id=1 author=korkin25 source=telegram at=2026-07-24T12:30:00Z -->
Pulled-back comment text.
```

Notes:

- **Frontmatter schema:** canonical, resolved in `docs/ticket-schema.md`
  (`JN-D3`). Identities are canonical handles resolved via
  `.jira_nano/users.yaml`; the comment log uses HTML-comment-delimited blocks.
- **Git history is the audit trail.** Who changed what and when is answered by
  `git log`/`git blame` on the ticket file — no separate audit store.
- **Atomicity.** Each logical change (create, transition, comment, assign) is one
  commit with a Conventional-Commit message referencing the ticket id.

### 2.2 SQLite cache (derived, rebuildable)

The cache mirrors ticket frontmatter into indexed tables so search, filtering,
and board queries are fast without scanning every file. It holds no state that
cannot be regenerated.

- **Rebuild:** a full rebuild walks `tickets/*.md`, parses frontmatter, and
  repopulates the tables. Triggered on demand, on cache-miss/version-mismatch,
  and after external Git changes (e.g. `git pull`).
- **Incremental update:** after a local write, the affected row is upserted so
  the cache stays hot without a full walk.
- **Consistency rule:** on any doubt (schema bump, corruption, divergence),
  discard and rebuild from Git. The cache never wins a conflict against the
  files.
- **Not committed:** the cache file(s) are `.gitignore`d.

## 3. Telegram mirror flow

The Telegram integration is a **communication mirror, not storage** — it
replaces Jira-style email notifications. It is driven by a **Telegram Bot** (Bot
API), which lets the bot manage forum **topics** and post to **threads** in a
project group.

Intended flow:

1. **Assignment ping.** When a ticket is assigned, the bot posts to the ticket's
   topic/thread and `@mentions` the assignee, so the human is notified where they
   already work.
2. **Status via icons.** Ticket status is reflected through topic/message icons
   (and/or emoji), giving an at-a-glance board inside Telegram.
3. **Update posts.** Ticket updates (transition, edit, new link from a MR/PR) are
   posted as messages into the ticket's thread.
4. **Comment pull-back.** Human comments written in Telegram are read by the bot
   and written back into the ticket file's comment log, then committed — so the
   Git store stays the single source of record.

Topic/thread management (create a forum topic per ticket or per epic, route
messages to the right thread) is handled by the bot. See §7 for why a bot rather
than a userbot.

## 4. MCP + API surface

A single service layer backs two front doors with the same operation set:

| Operation | Purpose |
|-----------|---------|
| `create` | Create a new ticket file (`JN-<n>`) |
| `update` | Edit frontmatter/body fields |
| `transition` | Change status via an allowed workflow transition |
| `assign` | Set/change the assignee (triggers a Telegram ping) |
| `comment` | Append a comment to the ticket log |
| `search` | Full-text / field search (served by the SQLite cache) |
| `list` | List tickets with filters |
| `board` | Board view grouped by status |

- **MCP server:** exposes these as MCP tools. The tool shape is kept **close to
  common Jira MCP servers** so existing AI workflows are drop-in with minimal
  remapping.
- **HTTP API:** the same operations for non-MCP clients (scripts, the Telegram
  bot, Git-host webhook handlers).
- **Validation:** every mutating call validates the requested transition against
  the configured workflow (`docs/status-model.md`) before writing to Git.

## 5. Git-host integration

Links code to tickets across **both GitLab and GitHub**.

- **Parsing:** detect `JN-<n>` ids in commit messages and MR/PR titles (and,
  optionally, branch names).
- **Linking:** add a `links` entry to the ticket frontmatter pointing at the
  commit / MR / PR.
- **Status moves:** on events (e.g. MR opened → `in-review`, merged → `done`),
  advance the ticket through the configured workflow.
- **Delivery:** driven by **webhooks** where available, with **polling** as a
  fallback for restricted environments. Both hosts are supported symmetrically.

## 6. Skill packaging

`jira_nano` is also shipped as an **Agent Skill** (`SKILL.md`) targeting the
Agent Skills standard (agentskills.io) for portability across OpenClaw / Claude /
other agents. The skill instructs an agent how to drive the tracker (via the MCP
server / API), so ticket management is available natively inside agent sessions.

## 7. Security & why a BOT (not a userbot)

- **Bot, not userbot.** The Telegram integration uses the **Bot API**, not a
  user account (MTProto userbot). A bot is:
  - **Multi-user and ToS-clean** — it acts as its own identity, not by
    automating a person's account (which risks account bans).
  - **Forum-capable** — bots can create/manage forum topics and post to threads,
    which is exactly the topic-per-ticket model the mirror needs.
  - **Webhook-friendly** — updates arrive over webhooks, no long-lived user
    session required for normal operation.
- **Credentials.** The bot token (and any Telethon session file used for
  administrative/migration tasks) is a **full-access credential**. Keep it in the
  environment or ignored local files, never in Git; apply least privilege; revoke
  on suspected leak.
- **No secrets in Git.** Enforced by `.gitignore`; configuration containing
  secrets is loaded from the environment.
- **Derived data excluded.** The SQLite cache is `.gitignore`d and always
  rebuildable, so it is never a place secrets or authoritative state can hide.

## 8. Technology stack (`JN-D2`)

The implementation language is **Python** (3.11 and 3.12, matching CI). The
language is fixed; the library picks below the first row are sensible defaults and
may be adjusted per phase.

| Concern | Choice | Notes |
|---------|--------|-------|
| **Language** | **Python 3.11 / 3.12** | Fixed (`JN-D2`); CI already targets both. |
| MCP server | official `mcp` SDK (FastMCP) | Jira-shaped tool surface. |
| HTTP API | FastAPI + uvicorn | Shares the one service layer. |
| Telegram bot | aiogram | Bot API, webhook-driven. |
| SQLite cache | stdlib `sqlite3` | Derived, rebuildable. |
| Frontmatter | PyYAML / ruamel.yaml | Parse & serialize ticket YAML. |
| Git store | `git` via subprocess (or pygit2) | One commit per change. |
| Tooling | ruff, pytest, bandit, pip-audit | Already wired into CI. |
| Env / distribution | `uv` for reproducible envs + `uv tool install`; single-file build (PyInstaller/shiv) evaluated later | Mitigates Python's weaker portability. |

Portability was a stated priority; since Python ships no static binary by default,
distribution leans on `uv` for reproducible installs, with a single-file build
evaluated when packaging (`JN-25`..`JN-27`) lands.
