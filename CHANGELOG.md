# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

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

- Initial documentation and non-code skeleton: `CLAUDE.md` (project rules,
  language rules, autonomous development workflow, conventions), `README.md`,
  `docs/architecture.md`, `docs/features.md`, `docs/status-model.md` (draft),
  `AGENTS.md`, `TODO.md`, `.gitignore`, `LICENSE` (GPL-3.0), and a minimal
  GitHub Actions CI stub (`.github/workflows/ci.yml`).
