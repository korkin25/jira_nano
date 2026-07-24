# TODO

## Current state / next action

**Project initialized:** documentation, rules, and non-code skeleton are in
place (`CLAUDE.md`, `README.md`, `docs/`, `CHANGELOG.md`, `LICENSE`,
`.gitignore`, `AGENTS.md`, CI stub). No application code exists yet.

**DEVELOPMENT happens in a separate chat** — this session only scaffolds the
repository.

**Next action:** **start Phase 1** — all Phase-1-blocking decisions are resolved:
`JN-D1` (workflow, `docs/status-model.md`), `JN-D2` (stack = **Python**,
`docs/architecture.md` §8), `JN-D3` (ticket schema, `docs/ticket-schema.md`).
`JN-D4` (MCP-vs-API priority) stays open but only affects Phase 2 ordering.
(Reminder: implementation happens in the separate dev chat.)

## Legend

- ⬜ `planned` — agreed but not started.
- 🟡 `in-progress` — actively being worked on.
- ✅ `done` — completed **and verified by a passing test**; moves to
  `CHANGELOG.md`.

## Maintenance rule

- When a task is ✅ done, move it out of this file into `CHANGELOG.md` (into the
  matching section), in the same change.
- Delete a phase/section here once it has no open tasks left.
- **Never mark a task done without a passing test.**

## Task IDs

- Local work items use `JN-<n>`; decisions use `JN-D<n>`.
- Numbering is **mandatory**, sequential, and **never reused** — a retired id
  stays retired.

## Open decisions

| ID | Decision | Notes |
|----|----------|-------|
| ~~JN-D1~~ | ~~Status/workflow model~~ | **Resolved** — canonical spec in `docs/status-model.md`. |
| ~~JN-D2~~ | ~~Stack / language~~ | **Resolved** — Python 3.11/3.12; stack in `docs/architecture.md` §8. |
| ~~JN-D3~~ | ~~Ticket-file layout~~ | **Resolved** — canonical schema in `docs/ticket-schema.md`. |
| JN-D4 | MCP-vs-API priority | Which surface ships first (MCP tools vs HTTP API) given the shared service layer. |

## Phase 1 — Core (git ticket store + sqlite cache + CRUD + search)

| ID | Status | Task | Details |
|----|--------|------|---------|
| JN-1 | ⬜ | Ticket-file schema | Implement parse/serialize/validate per `docs/ticket-schema.md` (spec locked by `JN-D3`). |
| JN-2 | ⬜ | Git ticket store | Read/write/parse `tickets/JN-<n>.md`; commit per change. |
| JN-3 | ⬜ | Ticket id allocation | Sequential `JN-<n>` allocator, never reused. |
| JN-4 | ⬜ | SQLite cache schema | Tables/indexes mirroring frontmatter. |
| JN-5 | ⬜ | Cache rebuild | Full rebuild from `tickets/*.md`. |
| JN-6 | ⬜ | Cache incremental upsert | Update a single row after a local write. |
| JN-7 | ⬜ | CRUD service layer | Create / read / update over the store. |
| JN-8 | ⬜ | Search + list + board | Cache-backed search, filtered list, board view. |

## Phase 2 — MCP + API

| ID | Status | Task | Details |
|----|--------|------|---------|
| JN-9 | ⬜ | Shared service API | One layer for all mutations + validation. |
| JN-10 | ⬜ | Transition validation | Enforce workflow (`JN-D1`) on every mutation. |
| JN-11 | ⬜ | MCP server | Expose create/update/transition/assign/comment/search/list/board. |
| JN-12 | ⬜ | Jira-close tool shape | Align tool names/args with common Jira MCP servers. |
| JN-13 | ⬜ | HTTP API | Same operations for non-MCP clients. |

## Phase 3 — Telegram bot mirror

| ID | Status | Task | Details |
|----|--------|------|---------|
| JN-14 | ⬜ | Bot skeleton | Telegram **Bot API** app (webhooks); token from env. |
| JN-15 | ⬜ | Forum topics/threads | Create/manage a thread per ticket (or epic). |
| JN-16 | ⬜ | Assignment pings | `@mention` the assignee on assignment. |
| JN-17 | ⬜ | Status icons | Reflect ticket status via topic/message icons. |
| JN-18 | ⬜ | Update posts | Post ticket updates into the ticket thread. |
| JN-19 | ⬜ | Comment pull-back | Write Telegram comments back into ticket files + commit. |

## Phase 4 — Git-host integration (GitLab / GitHub)

| ID | Status | Task | Details |
|----|--------|------|---------|
| JN-20 | ⬜ | `JN-<n>` parser | Detect ids in commit messages and MR/PR titles. |
| JN-21 | ⬜ | GitLab integration | Webhook/poll → link + transition. |
| JN-22 | ⬜ | GitHub integration | Webhook/poll → link + transition, symmetric to GitLab. |
| JN-23 | ⬜ | Link writer | Add commit/MR/PR entries to ticket `links`. |
| JN-24 | ⬜ | Event → transition map | Map host events onto workflow transitions. |

## Phase 5 — Skill packaging

| ID | Status | Task | Details |
|----|--------|------|---------|
| JN-25 | ⬜ | `SKILL.md` | Agent Skill targeting the agentskills.io standard. |
| JN-26 | ⬜ | Skill + MCP wiring | Let agents drive the tracker via skill + MCP. |
| JN-27 | ⬜ | Packaging/distribution | Package the skill for OpenClaw / Claude / others. |
