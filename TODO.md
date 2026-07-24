# TODO

## Current state / next action

**JN-47 in progress** (2026-07-25): 🟡 harden the **xenon complexity gate** from
report-mode (`continue-on-error`) to a **hard CI gate**. The gate
(`xenon --max-absolute C --max-modules B --max-average A src`) currently fails
because `githost/github.py` ranks **C** (its `parse_github` has CC 14). Plan:
refactor `parse_github` into small helpers (target rank A) + extract the shared
commit-id dedup into `githost/parser.py:collect_commit_ids` (reused by the GitLab
parser), add `auto-tests/group-a/complexity-gate.sh`, then drop `continue-on-error`.

| Test | Group | Status |
|------|-------|--------|
| `auto-tests/group-a/complexity-gate.sh` (xenon hard gate green) | (a) | 🟡 |
| existing githost parser suite stays green (behavior unchanged) | (a) | 🟡 |

**JN-46 done** (2026-07-25): container image + Helm chart + GHCR publishing. Multi-stage
`Dockerfile` (non-root, serves `jira-nano-http` on :8080), `docker-compose.yml`, Helm
`chart/` (StatefulSet + PVC git store, `jira-nano init` initContainer, voice-model PVC).
CI gains checkov/hadolint/trivy/semgrep/radon-xenon + pushes image & OCI chart to GHCR.
`helm lint`/`template` pass locally; Docker build validated. In `CHANGELOG.md` (`[Unreleased]`).

**JN-45 done** (2026-07-25): governance docs mirrored with `tg_notes` — `CLAUDE.md` now
carries the Documentation-sync table, the Testing policy (groups a/b/c, TDD-first, release
gate) and the extended MANDATORY Per-task lifecycle; features moved to root `Features.md`;
`docs/tests.md` + `auto-tests/` scaffolds added. In `CHANGELOG.md` (`[Unreleased]`).

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

**Phase 4 (Git-host GitLab/GitHub) is COMPLETE** — `JN-20`, `JN-24`, `JN-23`,
`JN-36`, `JN-21`, `JN-22`, `JN-37` (parser, event→transition, link writer, webhook
receiver, GitLab, GitHub, polling).

**Phase 5 (Skill packaging) is COMPLETE** — `JN-25`, `JN-26`, `JN-38`, `JN-27`
(SKILL.md, skill+MCP wiring, CLI, packaging).

🏁 **ALL FIVE PHASES COMPLETE** — every task (`JN-1`…`JN-38`, `JN-D1`…`JN-D6`),
including the previously-deferred `JN-34` (remote MCP over streamable-HTTP), is
implemented, TDD, and merged. Nothing deferred.

**Phase 6 (post-1.0 Telegram polish + live testing):**

- `JN-39` — Telegram message design overhaul (monospace id, bright circle status
  palette, `<blockquote>` ticket/board views) — **done**, merged.
- `JN-40` — Telegram **auto-trigger**: change-feed → mirror on a background poller
  (`telegram/mirror.py`; `jira-nano-bot` posts automatically on ticket changes) —
  **done**, merged.
- `JN-41` — Static per-status **banners** sent as photo + caption, shipped as
  package assets, no runtime rendering (`telegram/banners.py`) — **done**, merged.
- `JN-42` — Automated **live** end-to-end tests (mirror + auto-trigger + banners),
  opt-in via `JIRA_NANO_LIVE=1` — **done**, merged.
- `JN-43` — **Voice-message transcription**: voice reply in a topic → transcribe
  via a pluggable STT backend → pull the text into the ticket as a comment →
  delete the original audio — **done**, merged (default local Whisper via the
  `[voice]` extra, loaded on demand; optional OpenAI cloud via `JIRA_NANO_STT=cloud`).
- `JN-44` — **Portable voice / turnkey model**: `jira-nano-bot` provisions the
  local Whisper model at startup (cached on disk, no manual step) with
  `jira-nano-voice-setup` for explicit pre-fetch; `build_transcriber` auto-selects
  cloud when `OPENAI_API_KEY` is set, else the portable local Whisper — **done**,
  merged.

**All planning decisions are resolved:**

- `JN-D1` — status/workflow model → `docs/status-model.md`
- `JN-D2` — stack = **Python** (3.11/3.12) → `docs/architecture.md` §8
- `JN-D3` — ticket-file schema → `docs/ticket-schema.md`
- `JN-D4` — **MCP ships before HTTP**; internal callers in-process → `docs/architecture.md` §4
- `JN-D5` — HTTP API = drop-in **Jira REST** (v2 + v3) → `docs/http-api.md`
- `JN-D6` — MCP tool surface (copies Jira MCP servers) → `docs/mcp-tools.md`

**Next action:** finish **JN-47** (xenon → hard gate). Then optional: PyPI publish
(a separate explicit step — `uv publish`, installs via `pipx`).

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

## Not built (by decision — future work)

All planned tasks (`JN-1`…`JN-38`) and decisions (`JN-D1`…`JN-D6`) are done and
released. The following were **deliberately deferred or scoped out** and remain
open for a future version:

- **Deferred to v2** (`JN-D6`): worklogs / time tracking, sprints & agile,
  versions / releases, attachments (files-in-git story).
- **Jira-compat stubs** (`JN-D6` / `JN-D5`): field-metadata (`createmeta`/
  `editmeta`), projects/components, and generic issue links (blocks/relates)
  beyond `parent` — currently minimal/absent.
- **Auth** (`JN-D5`): OAuth 2.0 authorization-code flow (only `client_credentials`
  is implemented); full Markdown↔ADF node coverage (common nodes only).
- **Out of scope** (`JN-D6`): JSM / service desk, proforma forms, SLA, and the
  other Atlassian products.
- **Packaging** (`JN-D2`): single-file build (PyInstaller/shiv) — evaluated, not
  built.
- **Housekeeping:** the unused `cache.Cache` facade class is a vestigial stub
  (the cache works via the module functions).

