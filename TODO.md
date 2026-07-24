# TODO

## Current state / next action

**Project initialized:** documentation, rules, and non-code skeleton are in
place (`CLAUDE.md`, `README.md`, `docs/`, `CHANGELOG.md`, `LICENSE`,
`.gitignore`, `AGENTS.md`, CI stub). The **Phase 1 package skeleton** is in place
(`pyproject.toml`, `src/jira_nano/`, `tests/`).

**Phase 1 (Core) is COMPLETE** — all ten tasks implemented TDD and merged to
`main`: `JN-1`, `JN-28`, `JN-4`, `JN-2`, `JN-3`, `JN-5`, `JN-6`, `JN-29`, `JN-7`,
`JN-8` (models, git store, SQLite cache, config/users, CRUD service, cache-backed
queries, background sync). 66 tests green; ruff + mypy clean. Released **v0.1.0**;
CI runs the real suite.

**Phase 2 in progress:** `JN-9` (service API), `JN-10` (workflow engine:
transitions/guards/blocked) done. **Next: `JN-33`.**

**All planning decisions are resolved:**

- `JN-D1` — status/workflow model → `docs/status-model.md`
- `JN-D2` — stack = **Python** (3.11/3.12) → `docs/architecture.md` §8
- `JN-D3` — ticket-file schema → `docs/ticket-schema.md`
- `JN-D4` — **MCP ships before HTTP**; internal callers in-process → `docs/architecture.md` §4
- `JN-D5` — HTTP API = drop-in **Jira REST** (v2 + v3) → `docs/http-api.md`
- `JN-D6` — MCP tool surface (copies Jira MCP servers) → `docs/mcp-tools.md`

**Next action:** implement **`JN-33`** (Jira issue field mapper), TDD.

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

## Phase 2 — MCP + API

> **Order:** `JN-33` → `JN-30` → `JN-11` → `JN-12` → `JN-31` → `JN-32` → `JN-13`.
> (`JN-9`, `JN-10` ✅ done.) **MCP ships before HTTP** (`JN-D4`). Adapters are thin: a
> shared presentation layer — Jira field mapper (`JN-33`) + JQL parser (`JN-30`) —
> sits between the one service layer and both the MCP and HTTP adapters. Internal
> components (bot, git-host handlers) call the service layer **in-process**, not
> via HTTP. `JN-34` (remote MCP transport) is a deferred add-on, off the critical
> path.

| ID | Status | Task | Details |
|----|--------|------|---------|
| JN-33 | ⬜ | Jira issue field mapper | Ticket ↔ Jira issue JSON per `docs/http-api.md` (summary/statusCategory/issuetype/**Flagged**/parent/labels/comments/links; user `name` v2 / `accountId` v3). Shared by MCP + HTTP. |
| JN-30 | ⬜ | JQL subset parser | Parse the `docs/http-api.md` JQL subset → cache query (`JN-8`). Shared by MCP + HTTP search. |
| JN-11 | ⬜ | MCP server (stdio) | FastMCP over stdio exposing the `docs/mcp-tools.md` v1 tools; thin adapters over the service; search via `JN-30`, returns via `JN-33`. |
| JN-12 | ⬜ | Jira-close tool shape | Names/args/returns match `mcp-atlassian` (`docs/mcp-tools.md`); delete→archive; `jira_` prefix; golden conformance. **MCP ships here.** |
| JN-31 | ⬜ | Markdown↔ADF converter | Convert bodies MD↔ADF for v3 (headings/lists/code/links/emphasis; unknown→text). |
| JN-32 | ⬜ | HTTP auth | Basic + Bearer PAT + OAuth 2.0 (auth-code + client-credentials); secrets from env. |
| JN-13 | ⬜ | HTTP API | FastAPI `/rest/api/{2,3}/` (+`latest`→v3) per `docs/http-api.md`; endpoints→service, JQL `JN-30`, bodies `JN-33`(+`JN-31`), auth `JN-32`, Jira error envelope, v2 startAt vs v3 nextPageToken. Ships after MCP. |
| JN-34 | ⬜ | MCP streamable-HTTP transport | Deferred add-on: expose the MCP server (`JN-11`) over remote streamable-HTTP in addition to stdio. |

## Phase 3 — Telegram bot mirror

> **Order:** `JN-14` → `JN-15` → `JN-35` → `JN-17` → `JN-16` → `JN-18` → `JN-19`.
> The bot is an internal component — it calls the service layer **in-process**
> (`JN-D4`) and reacts to committed ticket changes via the git change-feed
> (`JN-35`), so it mirrors changes from every source (MCP/HTTP/CLI/git pull). The
> ticket↔topic mapping is stored as a `links[]` entry on the ticket.

| ID | Status | Task | Details |
|----|--------|------|---------|
| JN-14 | ⬜ | Bot skeleton | aiogram Bot API app (webhooks; token from env; forum supergroup from config); in-process service access (`JN-D4`). |
| JN-15 | ⬜ | Forum topic management | One topic per ticket (and epic); persist the ticket↔topic mapping as a `links[]` entry; reuse existing. |
| JN-35 | ⬜ | Git change-feed | Derive semantic per-ticket events (status/assignee/blocked/comment/link diffs) from committed changes (on `JN-29`); consumed by the mirror. |
| JN-17 | ⬜ | Status icons/colors | Map status→topic color + title emoji (`JN-D1`); 🚫 on `blocked`; `editForumTopic` on change. |
| JN-16 | ⬜ | Assignment pings | `@mention` the assignee (Telegram handle via `users.yaml`) in the ticket topic on assign. |
| JN-18 | ⬜ | Update posts | Post change deltas (transition/edit/new link) from the feed into the ticket topic. |
| JN-19 | ⬜ | Comment pull-back | Human topic message → `comment` via the service (commit-first→cache), `source=telegram`, author via `users.yaml`. |

## Phase 4 — Git-host integration (GitLab / GitHub)

> **Order:** `JN-20` → `JN-24` → `JN-23` → `JN-36` → `JN-21` → `JN-22` → `JN-37`.
> A shared webhook receiver (`JN-36`) normalizes GitLab/GitHub payloads into one
> event model, so the host adapters stay thin and symmetric; polling (`JN-37`) is
> the fallback where webhooks are unavailable. The receiver is separate from the
> Jira REST API (`JN-D4`).

| ID | Status | Task | Details |
|----|--------|------|---------|
| JN-20 | ⬜ | `JN-<n>` parser | Detect ids in commit messages, MR/PR titles (opt. branches); no false positives. |
| JN-24 | ⬜ | Event → transition map | Config map (`JN-D1`): forward auto-advance along the legal path; guard auto-assigns the MR/PR author; skip+note if unreachable. |
| JN-23 | ⬜ | Link writer | Append commit/MR/PR to `links[]` via the service; idempotent (no dupes). |
| JN-36 | ⬜ | Webhook receiver + event model | HTTP listener `/webhooks/{gitlab,github}` (separate from the Jira REST API, `JN-D4`); verify signature; normalize into `{host,kind,ref,url,ids,author}`. |
| JN-21 | ⬜ | GitLab integration | Map GitLab push/MR payloads → the common event; drive `JN-23`+`JN-24`. |
| JN-22 | ⬜ | GitHub integration | Symmetric: GitHub push/PR payloads → the common event; same pipeline. |
| JN-37 | ⬜ | Polling fallback | Poll host APIs for MRs/commits where webhooks are unavailable; same pipeline. |

## Phase 5 — Skill packaging

> **Order:** `JN-25` → `JN-26` → `JN-38` → `JN-27`.

| ID | Status | Task | Details |
|----|--------|------|---------|
| JN-25 | ⬜ | `SKILL.md` | agentskills.io format: how to drive jira_nano via MCP/CLI; when-to-use triggers. |
| JN-26 | ⬜ | Skill + MCP wiring | Skill instructs agents to use the MCP server; example flows; bundle MCP config. |
| JN-38 | ⬜ | CLI | Thin CLI over the service layer for humans/scripts (used by the skill and packaging). |
| JN-27 | ⬜ | Packaging/distribution | Installable bundle (skill + MCP entrypoint) via `uv tool`/pipx; single-file build eval (`JN-D2`); publish steps. |
