# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

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
