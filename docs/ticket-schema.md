# Ticket file schema

> **Status: RESOLVED (`JN-D3`).** Canonical specification of `tickets/JN-<n>.md`.
> Supersedes the draft in `docs/architecture.md` §2.1.

## Overview

One file per ticket: `tickets/JN-<n>.md`. It has two parts:

1. **YAML frontmatter** — structured fields mirrored into the SQLite cache.
2. **Markdown body** — a free-form `## Description` plus an append-only
   `## Comments` log.

The file is the **source of record**; `git log`/`git blame` on it is the audit
trail. Every logical change (create, transition, comment, assign, …) is one
commit with a Conventional-Commit message referencing the ticket id.

## Full example

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

Free-form Markdown body describing the work.

## Comments

<!-- c id=1 author=korkin25 source=telegram at=2026-07-24T12:30:00Z -->
Pulled-back comment — multi-line, **Markdown** works.

<!-- c id=2 author=claude source=mcp at=2026-07-24T13:00:00Z -->
Agent note.
```

## Frontmatter fields

| Field | Type | Required | Default | Notes |
|-------|------|----------|---------|-------|
| `id` | `JN-<n>` | yes | — | Must match the filename. |
| `type` | `task` \| `bug` \| `epic` | yes | `task` | Issue type. |
| `title` | string (single line) | yes | — | Human-readable summary. |
| `status` | workflow state | yes | `todo` | Enum from the configured workflow (`JN-D1`). |
| `priority` | `low` \| `medium` \| `high` \| `urgent` | no | `medium` | Fixed four-level scale. |
| `assignee` | canonical handle \| `null` | no | `null` | Single assignee (Jira-style). |
| `reporter` | canonical handle | yes | — | Who created the ticket. |
| `watchers` | list of canonical handles | no | `[]` | Extra Telegram ping targets. |
| `labels` | list of strings | no | `[]` | Free-form tags. |
| `blocked` | bool | no | `false` | Impediment flag (`JN-D1`), orthogonal to `status`. |
| `blocked_reason` | string | conditional | — | Present **only when** `blocked: true`. |
| `resolution` | `wontfix` \| `duplicate` \| `obsolete` | conditional | — | Present **only when** `status: archived`. |
| `parent` | `JN-<n>` | conditional | — | Present **only when set**; epic/subtask link. |
| `links` | list of link objects | no | `[]` | Git-host links (see below). |
| `created` | ISO-8601 UTC | yes | — | Set once at creation. |
| `updated` | ISO-8601 UTC | yes | — | Bumped on every change. |

### Field ordering

Serialized in this deterministic order to minimize diffs:

```
id, type, title, status, priority, assignee, reporter, watchers, labels,
blocked, blocked_reason, resolution, parent, links, created, updated
```

### Presence rules

- **Always required:** `id`, `type`, `title`, `status`, `reporter`, `created`,
  `updated`.
- **Always present (with defaults):** `priority`, `assignee` (may be `null`),
  `watchers`, `labels`, `blocked`, `links` — emitted even when empty so the shape
  is uniform and predictable for agents.
- **Conditional (omitted unless applicable):** `blocked_reason` (only when
  blocked), `resolution` (only when archived), `parent` (only when set).

### Timestamps

Stored as ISO-8601 UTC (`2026-07-24T12:30:00Z`). Git history is the authoritative
audit; these fields are a convenience mirror so the cache can sort by
`created`/`updated` without walking `git log` per ticket.

## `links`

A list of objects; git-host integration (`JN-D1`, Phase 4) appends to it.

| Key | Type | Required | Notes |
|-----|------|----------|-------|
| `type` | `commit` \| `mr` \| `pr` \| `branch` \| `issue` | yes | Kind of link. |
| `host` | `gitlab` \| `github` | yes | Origin host. |
| `url` | string | yes | Canonical URL. |
| `ref` | string | no | Short handle: `abc1234`, `!42`, `#42`. |

## Identities & the user directory

Ticket fields (`assignee`, `reporter`, `watchers`, comment `author`) hold a
**canonical handle** — a project-internal username, not a platform-specific one.
A separate versioned file resolves handles to platform identities so Telegram
pings and GitLab/GitHub author matching work regardless of naming differences:

```yaml
# .jira_nano/users.yaml
korkin25:
  name: "Kirill Korkin"
  telegram: "@korkin25"
  gitlab: korkin25
  github: korkin
  email: korkin@example.com
  # account_id: "opaque-id"   # optional; Jira REST v3 accountId (JN-D5). Default: the handle.
```

`users.yaml` lives alongside `workflow.yaml` under `.jira_nano/`. It is **not**
secret and **is** versioned (unlike credentials). All handles referenced by a
ticket must resolve here.

## Body: `## Description`

Free-form Markdown. No structural constraints beyond being the content under the
`## Description` heading, up to the `## Comments` heading (or end of file).

## Body: `## Comments`

An **append-only** log. Each comment is one block:

```
<!-- c id=<n> author=<handle> source=<telegram|mcp|api|githost> at=<ISO-8601 UTC> -->
<free Markdown, until the next comment header or end of file>
```

- The `<!-- c … -->` header carries machine-parseable metadata and is invisible
  in rendered Markdown; the body below it is free Markdown (multi-line safe).
- `id` — sequential per ticket, never reused (next = max existing + 1).
- `author` — canonical handle (resolvable via `users.yaml`).
- `source` — origin channel: `telegram` (pull-back), `mcp`, `api`, or `githost`
  (auto-notes from git-host events).
- `at` — ISO-8601 UTC.
- **Edits** (e.g. a Telegram edit pulled back) replace the block body in place and
  may add `edited=<ISO-8601 UTC>` to the header.

## Validation rules

A write is rejected unless:

1. `id` matches the filename and the `JN-<n>` scheme.
2. `status` is a state in the configured workflow; the attempted transition is
   legal (`JN-D1`).
3. `type` ∈ {task, bug, epic}; `priority` ∈ the four-level scale.
4. `blocked_reason` appears **iff** `blocked: true`; `resolution` appears **iff**
   `status: archived`.
5. `parent`, when present, references an existing ticket with no cycles.
6. Every handle (`assignee`, `reporter`, `watchers`, comment `author`) resolves
   in `.jira_nano/users.yaml`.
7. `created`/`updated` are valid ISO-8601 UTC and `updated >= created`.

## Relation to the SQLite cache

Every scalar frontmatter field maps to an indexed column; `labels`, `watchers`,
and `links` map to join tables. The cache is derived and rebuildable from these
files at any time (`docs/architecture.md` §2.2) — the schema here is authoritative.
