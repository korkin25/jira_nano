# TODO

## Current state / next action

**Project initialized:** documentation, rules, and non-code skeleton are in
place (`CLAUDE.md`, `README.md`, `docs/`, `CHANGELOG.md`, `LICENSE`,
`.gitignore`, `AGENTS.md`, CI stub). No application code exists yet.

**DEVELOPMENT happens in a separate chat** — this session only scaffolds the
repository.

**All planning decisions are resolved:**

- `JN-D1` — status/workflow model → `docs/status-model.md`
- `JN-D2` — stack = **Python** (3.11/3.12) → `docs/architecture.md` §8
- `JN-D3` — ticket-file schema → `docs/ticket-schema.md`
- `JN-D4` — **MCP ships before HTTP**; internal callers in-process → `docs/architecture.md` §4
- `JN-D5` — HTTP API = drop-in **Jira REST** (v2 + v3) → `docs/http-api.md`
- `JN-D6` — MCP tool surface (copies Jira MCP servers) → `docs/mcp-tools.md`

**Next action:** **start Phase 1** (implementation, in the separate dev chat).

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

## Phase 1 — Core (git ticket store + sqlite cache + CRUD + search)

> **Suggested order:** `JN-1` → `JN-28` → `JN-4` → `JN-2` → `JN-3` → `JN-5` →
> `JN-6` → `JN-29` → `JN-7` → `JN-8`.
> **Conventions:** **Git is the single source of truth**; the local SQLite cache
> mirrors everything (tickets + users) for speed and serves **all** reads
> (`get`/`list`/`search`/`board`). **Writes commit to Git first, then update the
> cache** — never the reverse. Status transitions (`JN-D1`) are validated in
> Phase 2 (`JN-10`) — Phase 1 `create` sets initial `todo` and `update` edits
> fields only. The user directory (`.jira_nano/users.yaml`) is git-backed and
> mirrored into the cache like tickets.

| ID | Status | Task | Details |
|----|--------|------|---------|
| JN-1 | ⬜ | Ticket schema & (de)serialization | Models + parse/serialize (deterministic key order, presence rules) + field validation per `docs/ticket-schema.md` (`JN-D3`). |
| JN-28 | ⬜ | Config & user-directory loader | Load `.jira_nano/users.yaml` (git source of record) + `workflow.yaml` skeleton; validate handles; mirror users into the cache. |
| JN-4 | ⬜ | SQLite cache schema | Full-ticket rows (frontmatter + body + comments) + join tables (`labels`/`watchers`/`links`) + `users` + FTS + `schema_version` — serves all reads. |
| JN-2 | ⬜ | Git ticket store (**pygit2**) | Read/write/list `tickets/JN-<n>.md`; commit per change (Conventional-Commit w/ id); read history. |
| JN-3 | ⬜ | Ticket id allocation | Sequential `JN-<n>` (max+1), never reused; lock for concurrent creates. |
| JN-5 | ⬜ | Cache rebuild | Full rebuild from `tickets/*.md` + `.jira_nano/` (users/workflow); idempotent. |
| JN-6 | ⬜ | Cache incremental upsert | Upsert one ticket's rows (or a user) after a local write, no full walk. |
| JN-29 | ⬜ | Background cache sync | Detect external git changes (stored HEAD SHA + pygit2 diff) and working-tree edits; refresh the cache incrementally. |
| JN-7 | ⬜ | CRUD service layer | Single entry, **MCP-first** API: `create` (initial `todo`), `get` (from cache), `update` (fields). Writes commit to Git first, then upsert the cache (`JN-6`). |
| JN-8 | ⬜ | Search + list + board | Cache-backed `search` (FTS+filters), filtered `list`, `board` grouped by status. |

## Phase 2 — MCP + API

> **Order:** `JN-9` → `JN-10` → `JN-33` → `JN-30` → `JN-11` → `JN-12` → `JN-31` →
> `JN-32` → `JN-13`. **MCP ships before HTTP** (`JN-D4`). Adapters are thin: a
> shared presentation layer — Jira field mapper (`JN-33`) + JQL parser (`JN-30`) —
> sits between the one service layer and both the MCP and HTTP adapters. Internal
> components (bot, git-host handlers) call the service layer **in-process**, not
> via HTTP. `JN-34` (remote MCP transport) is a deferred add-on, off the critical
> path.

| ID | Status | Task | Details |
|----|--------|------|---------|
| JN-9 | ⬜ | Shared service API | Complete the service layer over Phase 1: `assign`, `comment` (add/edit), `watchers` (add/remove/get), `link` (epic `parent` + remote `links[]`); one validated facade, commit-first→cache. |
| JN-10 | ⬜ | Transition validation | Workflow engine (`JN-D1`): `get_transitions` + strict `transition` (guards, no force) + `set`/`clear_blocked` flag. |
| JN-33 | ⬜ | Jira issue field mapper | Ticket ↔ Jira issue JSON per `docs/http-api.md` (summary/statusCategory/issuetype/**Flagged**/parent/labels/comments/links; user `name` v2 / `accountId` v3). Shared by MCP + HTTP. |
| JN-30 | ⬜ | JQL subset parser | Parse the `docs/http-api.md` JQL subset → cache query (`JN-8`). Shared by MCP + HTTP search. |
| JN-11 | ⬜ | MCP server (stdio) | FastMCP over stdio exposing the `docs/mcp-tools.md` v1 tools; thin adapters over the service; search via `JN-30`, returns via `JN-33`. |
| JN-12 | ⬜ | Jira-close tool shape | Names/args/returns match `mcp-atlassian` (`docs/mcp-tools.md`); delete→archive; `jira_` prefix; golden conformance. **MCP ships here.** |
| JN-31 | ⬜ | Markdown↔ADF converter | Convert bodies MD↔ADF for v3 (headings/lists/code/links/emphasis; unknown→text). |
| JN-32 | ⬜ | HTTP auth | Basic + Bearer PAT + OAuth 2.0 (auth-code + client-credentials); secrets from env. |
| JN-13 | ⬜ | HTTP API | FastAPI `/rest/api/{2,3}/` (+`latest`→v3) per `docs/http-api.md`; endpoints→service, JQL `JN-30`, bodies `JN-33`(+`JN-31`), auth `JN-32`, Jira error envelope, v2 startAt vs v3 nextPageToken. Ships after MCP. |
| JN-34 | ⬜ | MCP streamable-HTTP transport | Deferred add-on: expose the MCP server (`JN-11`) over remote streamable-HTTP in addition to stdio. |

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
