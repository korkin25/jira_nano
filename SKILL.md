---
name: jira_nano
description: Manage tickets in a jira_nano tracker (a git-backed, Jira-compatible issue tracker) — create, read, search, transition, assign, comment, and link issues — through its MCP tools or CLI. Use whenever the user wants to create or update issues, move them through a workflow, or query a jira_nano / Jira-shaped board.
license: GPL-3.0-or-later
---

# jira_nano

`jira_nano` is a lightweight, AI-native issue tracker whose source of record is a
Git repository (one `tickets/JN-<n>.md` file per ticket) with a rebuildable SQLite
query cache. It exposes a **Jira-compatible** MCP tool surface and HTTP REST API,
so existing Jira agent workflows are drop-in.

## When to use

Use this skill when the user wants to:

- create, read, or update issues ("open a ticket", "file a bug");
- move an issue through the workflow ("start work", "send to review", "close");
- assign an issue or add a comment / watcher;
- search or list issues, or view the board.

## Workflow model

- **Statuses:** `todo` → `in-progress` → `in-review` → `done`, plus `archived`.
  Transitions are **strict** — only legal moves succeed (no force). Reopen via
  `done → todo` / `archived → todo`.
- **Ids** are `JN-<n>` (sequential, never reused). `blocked` is an orthogonal flag.

## Driving it via MCP (preferred)

The MCP server (`jira_nano.mcp_server`) exposes Jira-named tools:

| Tool | Purpose |
|------|---------|
| `jira_create_issue(summary, reporter, ...)` | create an issue |
| `jira_get_issue(issue_key)` | read one issue |
| `jira_update_issue(issue_key, ...)` | edit fields |
| `jira_search(jql)` | search (JQL subset) |
| `jira_get_transitions(issue_key)` / `jira_transition_issue(issue_key, status)` | workflow |
| `jira_assign_issue(issue_key, assignee)` | assign |
| `jira_add_comment(issue_key, body, author)` | comment |
| `jira_link_to_epic(issue_key, epic_key)` | epic hierarchy |

Returns are Jira issue JSON (`{ key, fields: { summary, status, ... } }`).

## Driving it via the CLI

`jira-nano <command>` mirrors the same operations for humans and scripts, e.g.
`jira-nano create --title "Fix login" --reporter me`.

## Notes

- Git is the source of truth; every change is a commit. Reads are served from the
  local cache.
- The HTTP API is a drop-in Jira REST surface at `/rest/api/{2,3}/…`.
