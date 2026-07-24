# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `JN-14`: Telegram bot skeleton (`jira_nano.telegram`, aiogram) — env-based
  config (bot token + forum chat id), `build_bot`, and `build_dispatcher` with
  in-process service access. `aiogram` is an optional extra (`jira-nano[telegram]`).

## [0.2.0] - 2026-07-24

### Added

- `JN-13`: HTTP API (`jira_nano.http.app`, FastAPI) — a drop-in **Jira REST**
  surface serving `/rest/api/{2,3,latest}/…`: issue CRUD (delete → archive),
  transitions, assignee, comments, v2 (`startAt`) and v3 (`nextPageToken`) search,
  `myself`, and an OAuth token endpoint; Jira error envelope; `mcp`/`http` are
  optional extras. **Phase 2 core (MCP + HTTP) complete.**
- `JN-32`: HTTP authentication (`jira_nano.http.auth`) — Basic, Bearer PAT, and
  OAuth 2.0 `client_credentials` (jira_nano issues its own bearer tokens);
  credentials loaded from the environment.
- `JN-31`: Markdown↔ADF converter (`jira_nano.jira.adf`) — paragraphs, headings,
  code blocks, bullet/ordered lists, and inline marks (strong/em/code/link); now
  used by the mapper for v3 bodies.
- `JN-12`: rounded out the MCP tool surface to match common Jira MCP servers —
  `jira_delete_issue` (→ archive), `jira_batch_create_issues`,
  `jira_get_project_issues`, `jira_edit_comment`, `jira_create_remote_issue_link`,
  `jira_get_user_profile`, `jira_search_assignable_users`; golden conformance tests.
- `JN-11`: MCP server (`jira_nano.mcp_server.build_server`, FastMCP/stdio) — thin
  tools over the service returning Jira-shaped issues; search via the JQL subset.
  `mcp` is an optional dependency (`jira-nano[mcp]`), keeping the core lightweight.
- `JN-30`: JQL subset parser + executor (`jira_nano.jira.jql`) — fields, `=`/`!=`/
  `~`/`IN`, `AND`/`OR`, and `ORDER BY`, compiled to SQL over the cache.
- `JN-33`: Jira issue field mapper (`jira_nano.jira.mapper`) — `to_jira_issue`
  (v2/v3 dialects: string vs ADF body, username vs accountId, statusCategory,
  Flagged, resolution, parent, comments) and `fields_from_jira`.
- `JN-10`: workflow engine — `get_transitions`, strict `transition` (validated
  against the configured workflow + guards, no force override), and the
  `set_blocked` / `clear_blocked` impediment flag.
- `JN-9`: extended service API — `assign`, `comment` / `edit_comment`,
  `add_watcher` / `remove_watcher` / `get_watchers`, `link_epic`, and `add_link`,
  all commit-first then cache-upsert via a shared `_mutate`.

## [0.1.0] - 2026-07-24

### Changed

- Refined the Phase 3–5 plans: added a git change-feed for outbound Telegram
  mirroring (`JN-35`), a shared git-host webhook receiver (`JN-36`) + polling
  fallback (`JN-37`), and a CLI (`JN-38`); the Telegram ticket↔topic mapping is a
  `links[]` entry (new `telegram` link type).
- Refined the Phase 2 plan: split out shared/support modules — Jira field mapper
  (`JN-33`), JQL subset parser (`JN-30`), Markdown↔ADF converter (`JN-31`), and
  HTTP auth (`JN-32`) — kept the MCP-before-HTTP order, and added a deferred
  remote MCP transport task (`JN-34`, streamable-HTTP).
- Refined the Phase 1 plan: chose **pygit2** for the git store, added a config /
  user-directory loader (`JN-28`) and a background cache-sync watcher (`JN-29`);
  the user directory (`.jira_nano/users.yaml`) is git-backed (source of record)
  and mirrored into the SQLite cache for speed. Clarified the storage model:
  **Git is the single source of truth**, the working files and SQLite are both
  local caches serving all reads (incl. `get`), and writes **commit to Git first,
  then update the cache**.
- Resolved decision `JN-D5`: HTTP API specced as a drop-in **Jira REST** surface
  in `docs/http-api.md` — serves **both v2 and v3** dialects (plain-string vs ADF
  bodies, username vs accountId, classic vs token-paginated search), mirrors the
  MCP tool surface (`JN-D6`), a pragmatic JQL subset, and Basic + Bearer PAT +
  OAuth 2.0 auth. Adds an optional `account_id` to the user directory.
- Resolved decision `JN-D6`: MCP tool surface specced in `docs/mcp-tools.md` —
  copies the `mcp-atlassian` Jira tool shape (names/args) scoped to a git-backed
  tracker; no hard delete (`jira_delete_issue` → `archived`), `jira_` prefix kept
  verbatim, worklogs/agile/attachments deferred to v2.
- Resolved decision `JN-D4`: **MCP ships before the HTTP API**; both are thin
  adapters over the shared service layer, and internal components (Telegram bot,
  git-host handlers) call that layer in-process rather than over HTTP
  (`docs/architecture.md` §4).
- Resolved decision `JN-D3`: canonical ticket-file schema in
  `docs/ticket-schema.md` — `JN-<n>.md` frontmatter (`type`/`parent` hierarchy,
  single `assignee` + `reporter` + `watchers`, four-level `priority`, `blocked`
  flag, `links`, ISO-8601 UTC timestamps), canonical-handle identities resolved
  via `.jira_nano/users.yaml`, and an append-only HTML-comment-delimited comment
  log.
- Resolved decision `JN-D2`: implementation language is **Python** (3.11/3.12);
  default stack (FastMCP, FastAPI, aiogram, stdlib `sqlite3`, `uv`) documented in
  `docs/architecture.md` §8.
- Resolved decision `JN-D1`: finalized the status/workflow model in
  `docs/status-model.md` — a Jira-conventional, fully user-configurable workflow
  with five default states (`todo` initial: `todo` → `in-progress` → `in-review`
  → `done`, plus `archived`), strictly enforced with no illegal transitions and
  no force override, an orthogonal `blocked` impediment flag (Jira-style),
  forward-only auto-advance on git-host events, a single `assignee` guard on
  `in-progress`, and per-repository workflow config.

### Added

- `JN-8`: cache-backed reads — `search` (FTS5 + field filters), `list_tickets`
  (status/assignee/priority/type/label), and `board` (grouped by status), exposed
  on `TicketService`. **Completes Phase 1 (Core).**
- `JN-7`: CRUD service layer (`TicketService`) — the single entry point;
  `create` (initial status, sequential id), `get` (from cache), `update`
  (fields), each committing to Git first, then upserting the cache.
- `JN-29`: background cache sync — detects external git changes (stored HEAD sha
  + pygit2 diff) and uncommitted working-tree edits, and refreshes the cache
  incrementally (full rebuild on first run).
- `JN-6`: incremental cache upsert — a single ticket (or user) update replaces
  its row, join rows, and FTS entry without a full walk; siblings untouched.
- `JN-5`: full cache rebuild from `tickets/*.md` + `.jira_nano/users.yaml`
  (idempotent), plus the shared cache row writers `upsert_ticket` / `upsert_user`.
- `JN-3`: sequential `JN-<n>` id allocator (`max + 1`, never reused).
- `JN-2`: git-backed ticket store (pygit2) — read/write/list `tickets/JN-<n>.md`,
  one commit per change, and per-ticket commit history.
- `JN-4`: SQLite cache schema — full-ticket rows, join tables
  (`labels`/`watchers`/`links`), `users`, an FTS5 index, and a `meta` table with
  the schema version; `create_schema` (idempotent) + `read_version`.
- `JN-28`: config & user-directory loader — repo paths, `.jira_nano/workflow.yaml`
  (with a built-in default per `JN-D1`), and `.jira_nano/users.yaml` with handle
  resolution.
- `JN-1`: ticket domain models (pydantic, with consistency validation) and
  byte-stable Markdown (de)serialization (`loads`/`dumps`) for `tickets/JN-<n>.md`.
- Phase 1 package skeleton: `pyproject.toml` (hatchling, pydantic/pygit2/PyYAML,
  ruff/pytest/mypy config) and `src/jira_nano/` typed stubs — `models`,
  `serialization`, `ids`, `config`, `users`, `store`, `cache/` (schema/rebuild/
  upsert/queries), `sync`, `service` — plus a `tests/` layout. All bodies raise
  `NotImplementedError`; implementation is TDD in the dev chat.
- Initial documentation and non-code skeleton: `CLAUDE.md` (project rules,
  language rules, autonomous development workflow, conventions), `README.md`,
  `docs/architecture.md`, `docs/features.md`, `docs/status-model.md` (draft),
  `AGENTS.md`, `TODO.md`, `.gitignore`, `LICENSE` (GPL-3.0), and a minimal
  GitHub Actions CI stub (`.github/workflows/ci.yml`).
