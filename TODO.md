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

**Phase 2 in progress:** `JN-9` (service API), `JN-10` (workflow engine), `JN-33`
(Jira mapper), `JN-30` (JQL parser), `JN-11` (MCP server), `JN-12` (Jira tools),
`JN-31` (ADF), `JN-32` (HTTP auth), `JN-13` (HTTP Jira REST v2+v3) done.

**Phase 2 core is COMPLETE** — MCP server + HTTP Jira REST API over the shared
service layer. `JN-34` (remote MCP streamable-HTTP transport) is a deferred
runtime add-on.

**Phase 3 (Telegram mirror) is COMPLETE** — `JN-14`, `JN-15`, `JN-35`, `JN-17`,
`JN-16`, `JN-18`, `JN-19` (skeleton, topics, change-feed, icons, pings, update
posts, comment pull-back).

**Phase 4 in progress:** `JN-20` (parser), `JN-24` (event→transition), `JN-23`
(link writer) done. **Next: `JN-36`.**

**All planning decisions are resolved:**

- `JN-D1` — status/workflow model → `docs/status-model.md`
- `JN-D2` — stack = **Python** (3.11/3.12) → `docs/architecture.md` §8
- `JN-D3` — ticket-file schema → `docs/ticket-schema.md`
- `JN-D4` — **MCP ships before HTTP**; internal callers in-process → `docs/architecture.md` §4
- `JN-D5` — HTTP API = drop-in **Jira REST** (v2 + v3) → `docs/http-api.md`
- `JN-D6` — MCP tool surface (copies Jira MCP servers) → `docs/mcp-tools.md`

**Next action:** implement **`JN-36`** (webhook receiver + normalized event model), TDD.

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

> **Phase 2 core done** (`JN-9`, `JN-10`, `JN-33`, `JN-30`, `JN-11`, `JN-12`,
> `JN-31`, `JN-32`, `JN-13` ✅). Only `JN-34` (deferred) remains. Adapters are thin: a
> shared presentation layer — Jira field mapper (`JN-33`) + JQL parser (`JN-30`) —
> sits between the one service layer and both the MCP and HTTP adapters. Internal
> components (bot, git-host handlers) call the service layer **in-process**, not
> via HTTP. `JN-34` (remote MCP transport) is a deferred add-on, off the critical
> path.

| ID | Status | Task | Details |
|----|--------|------|---------|
| JN-34 | ⬜ | MCP streamable-HTTP transport | Deferred add-on: expose the MCP server (`JN-11`) over remote streamable-HTTP in addition to stdio. |

## Phase 4 — Git-host integration (GitLab / GitHub)

> **Order:** `JN-36` → `JN-21` → `JN-22` → `JN-37`. (`JN-20`, `JN-24`, `JN-23` ✅ done.)
> A shared webhook receiver (`JN-36`) normalizes GitLab/GitHub payloads into one
> event model, so the host adapters stay thin and symmetric; polling (`JN-37`) is
> the fallback where webhooks are unavailable. The receiver is separate from the
> Jira REST API (`JN-D4`).

| ID | Status | Task | Details |
|----|--------|------|---------|
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
