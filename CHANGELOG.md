# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- **JN-51 — adopt the `ai-project-template` engineering standard (feature #51).** Universal
  agent-rule pickup: `CLAUDE.md` is the single source and `AGENTS.md`, `GEMINI.md`,
  `.cursorrules`, `.clinerules`, `.windsurfrules`, `.github/copilot-instructions.md` are
  symlinks to it, with `.cursor/rules/project.mdc` as a thin pointer and a per-turn
  `.claude/settings.json` hook re-injecting the context map. `CLAUDE.md` gained the
  **Start-here context-map router**, **Versioning** (GitVersion), **Safe autonomy**,
  **Agent security working agreements**, **Design-before-code**, and the cross-agent
  portability section. Added a **doc-sync** CI guard (`.github/workflows/doc-sync.yml`),
  **Dependabot**, **pre-commit** (gitleaks via Docker only), **CODEOWNERS**, PR/issue
  templates, `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `GitVersion.yml`, and a
  `.gitlab-ci.yml` mirror (using `open_ci_cd/templates`). The install-guide curl examples now
  use `$JIRA_NANO_TOKEN`/`$CLIENT_SECRET` placeholders instead of literal fake secrets, so the
  newly-added gitleaks gate stays clean.
- **JN-46 — container image, Helm chart & GHCR publishing.** Multi-stage
  `Dockerfile` (non-root uid 10000; default serves the HTTP Jira REST API on
  :8080), `docker-compose.yml` (init + API + optional bot/mcp-http profiles), and
  a Helm `chart/` adapted from the BNPL "application" chart — StatefulSet + PVC for
  the git ticket store & SQLite cache, `jira-nano init` initContainer, TCP probes,
  optional Service/Ingress/ServiceMonitor/HPA/PDB. The Whisper voice model is kept
  off the image and provisioned via a chart PVC (fetched on first use or preloaded),
  documented in `chart/README.md`. CI (GitHub Actions) gains a security & quality
  suite — checkov, hadolint, trivy, semgrep, radon/xenon — and publishes the image
  to `ghcr.io/korkin25/jira-nano` (main + tags) and the OCI chart to
  `ghcr.io/korkin25/charts/jira-nano` (tags), alongside the existing PyPI release.
  A second `docker-compose.voice.yml` (heavy, non-CI) builds a voice-enabled image
  (`EXTRAS=...,voice` + `WITH_FFMPEG=1`) for local STT testing; model weights stay
  out of the image on the models volume/PVC.

### Changed

- **JN-54 — stable releases now cut a GitHub Release.** `release.yml` gains a final
  `GitHub Release (stable only)` step, gated `if: github.ref_name == 'release'`, that tags
  `vX.Y.Z` at the merge commit and cuts a GitHub Release with auto-generated notes and the
  built sdist+wheel attached (`gh release create ... --generate-notes dist/*`); the job's
  `contents` permission was raised from `read` to `write` for it. A merge to `rc` stays
  **registry-only** — a PyPI pre-release with **no tag**, so pre-release tags never confuse
  GitVersion. Mirrors the canonical `ai-project-template` release workflow.
- **JN-53 — adopted the shared release standard (merge-to-publish, no tags).** Releasing is
  now a **merge, not a tag**: the new vendored `.github/workflows/release.yml` runs
  `on: push: branches: [rc, release]` — a merge to `rc` publishes a **PyPI pre-release**
  (`X.Y.ZrcN`), a merge to `release` publishes the clean stable `X.Y.Z`. The version comes
  entirely from **GitVersion** via a clean **6.x-native `GitVersion.yml`** (single knob
  `next-version`, no `tag-prefix`, no git tags — the old BNPL-style 5.x config that broke
  `next-version` parsing under GitVersion 6.8+ is gone). `pyproject.toml` moved from a **static
  `version`** to `dynamic = ["version"]` reading `src/jira_nano/__init__.py` (a `0.0.0`
  placeholder); `release.yml` injects the GitVersion number with `hatch version <semver>` at
  publish time. The manual-dispatch `publish.yml` is **removed**, superseded by `release.yml`.
  `CLAUDE.md` gains the **Versioning & releasing** section and a **`Features.md` scope rule**
  (only user-facing product features belong there; engineering/infra tasks live in
  `TODO.md`/`CHANGELOG.md`) — the infra feature entry #51 was moved out of `Features.md`.
- **JN-52 — tamed Dependabot noise + doc-sync exemption.** The `doc-sync` guard now skips
  dependency PRs (the `dependencies` label / `dependabot[bot]` actor) — a version bump carries
  no doc change and should not be forced to fake one. `dependabot.yml` now opens **one grouped
  PR per ecosystem** and **ignores breaking major bumps**; only minor/patch updates are proposed
  (majors are a deliberate migration task, not a red auto-PR).
- **JN-51 — CI is now a composition, and the branch model moved to `dev`/`rc`/`release`.**
  `.github/workflows/ci.yml` is wiring only — every job `uses:` a reusable workflow from
  `korkin25/open-ci-actions@v1` (`detect` → `version` → `python` / `sast` / `docker` / `helm` /
  `functional`), plus one bespoke `quality` job that preserves the JN-47 xenon **hard gate**
  (`complexity-gate.sh`). The old inline HTTP-API e2e job became the script-driven
  `auto-tests/group-a/validate-deploy.sh` (build image → boot `jira-nano-http` → authenticated
  probe; exit 0/77/other; probe host portable across GitHub and GitLab DinD). PyPI publishing
  stays in the vendored `publish.yml` (the reusable release workflow can't trusted-publish
  cross-repository). The old `main` branch is retired in favour of `feature/*` → `dev` → `rc` →
  `release`; `dev` is the default branch and versions come from GitVersion.
- **JN-47 — xenon complexity gate graduated to a hard CI gate.** The radon/xenon
  `quality` job is no longer `continue-on-error`: `xenon --max-absolute C
  --max-modules B --max-average A src` now blocks the build. To clear the baseline,
  `githost/github.py` was refactored (`parse_github` split into `_parse_pull_request`
  / `_parse_push`, dropping its complexity from C(14) to A(4)) and the shared
  push-commit id dedup was hoisted into `githost/parser.py:collect_commit_ids`
  (reused by the GitLab parser, which drops to B). Thresholds now live in
  `auto-tests/group-a/complexity-gate.sh` (single source of truth, runnable locally).
- **JN-45 — governance docs mirrored with `tg_notes`.** `CLAUDE.md` gains explicit,
  apply-without-being-asked sections: **Documentation sync** (trigger→update table),
  **Testing policy** (three test groups a/b/c, TDD-first, CI log analysis even on green,
  release gate), a **Feature backlog** rule (root `Features.md`), and the MANDATORY
  **Per-task lifecycle** extended to log → backlog → test-plan → branch → TDD → verify →
  record → MR. The features doc moved from `docs/features.md` to the root **`Features.md`**
  (numbered backlog: Current / Planned / Brainstorm / Delivered). New `docs/tests.md`
  (per-feature test catalog) and `auto-tests/` (group-a/b/c scripts + methodologies)
  scaffolds added. Stale "planning — nothing implemented" status lines corrected to
  "released".

## [0.5.0] - 2026-07-25

### Added

- Telegram **voice-message transcription** (`telegram/voice.py`,
  `telegram/transcribe.py`): a voice/audio reply in a ticket's forum topic is
  transcribed and pulled back into the ticket as a comment (prefixed 🎙), then the
  original audio message is deleted. The STT backend is pluggable — the default
  runs a local Whisper model (`faster-whisper`, `[voice]` extra, loaded on demand)
  and an optional cloud backend uses OpenAI (`JIRA_NANO_STT=cloud`). Heavy libs
  are lazy-imported, so the package still imports and runs without them. The bot
  provisions the local model at startup (cached on disk afterwards, no manual
  step) — `jira-nano-voice-setup` pre-fetches it explicitly — and the backend
  auto-selects cloud when `OPENAI_API_KEY` is set, else the portable local Whisper.
- Telegram **static status banners**: a pre-rendered banner image per status is
  shipped as a package asset (`telegram/assets/status_<name>.png`); the mirror
  sends the matching banner as a photo with the ticket details as the caption
  (`telegram/banners.py`, `TopicGateway.post_card`) — **no runtime image
  rendering**, it just loads the committed PNG and falls back to a plain text post
  when no banner matches or the caption exceeds Telegram's 1024-char limit. The
  banners are regenerated with `scripts/render_status_banners.py` (dev-only,
  needs Pillow).
- Telegram **auto-trigger** (`telegram/mirror.py`): `jira-nano-bot` now mirrors
  committed ticket changes automatically. A background poller advances a cursor
  over Git history (`telegram_head_sha` in the cache, separate from the sync
  cursor) and turns each new committed change into the right side effect —
  assignment pings, forum-topic renames on status/blocked changes, and update
  posts. It baselines on first run (no history replay) and self-heals a rewritten
  history. Runs alongside comment pull-back; skipped when `TELEGRAM_CHAT_ID` is
  unset. Poll interval via `JIRA_NANO_MIRROR_INTERVAL` (default 3s).
- Automated live end-to-end tests of the Telegram mirror (`tests/live/`,
  `live` marker): drive the real mirror code — topics, pings, banner cards, rich
  views, and the change-feed **auto-trigger** poller — against a configured forum
  supergroup and clean up after themselves. Opt-in via `JIRA_NANO_LIVE=1` +
  `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID`; skipped by default so CI stays green.
- Telegram rich views (`telegram/views.py`): `render_ticket` (a single-ticket
  field card) and `render_board` (a numbered board/sprint listing), both wrapping
  their structured content in a `<blockquote>` so listings read cleanly. Ticket
  ids stay monospace/copyable and links render as real hyperlinks.

### Changed

- Telegram mirror: redesigned message formatting. Pings and update posts share a
  consistent HTML layout — a header (status icon + bold title + monospace,
  easy-to-copy ticket id) plus a one-line change summary (`↳ …`); comments quote
  the body in an **expandable block quotation** (Bot API 7.0) and links render as
  real hyperlinks. Dynamic text is HTML-escaped; forum topic names stay plain text
  (Telegram does not format them). `telegram/format.py:ticket_ref` is the single
  place to later turn the id into a deep link.
- Default workflow status icons are now bright colored circles (🟡 todo, 🔵
  in-progress, 🟣 in-review, 🟢 done, ⚫ archived) instead of pictographs, for a
  clearer at-a-glance status colour in topic names and messages. Configurable per
  workflow via `.jira_nano/workflow.yaml`.

## [0.4.1] - 2026-07-24

### Changed

- `jira-nano-http` and `jira-nano-webhooks` now bind all interfaces (`0.0.0.0`)
  by default so they are reachable on the deploy host; set
  `JIRA_NANO_HTTP_HOST` / `JIRA_NANO_WEBHOOK_HOST` to `127.0.0.1` to restrict.

## [0.4.0] - 2026-07-24

### Added

- `jira-nano init` — bootstraps a repository (git init + a default
  `.jira_nano/workflow.yaml` and a `users.yaml` template) so a fresh setup needs
  no manual file creation.
- Run entry points for every surface, configured via env vars: `jira-nano-http`
  (HTTP Jira REST API), `jira-nano-bot` (Telegram long-polling), and
  `jira-nano-webhooks` (git-host receiver with the GitLab/GitHub parsers wired).

## [0.3.2] - 2026-07-24

### Changed

- CI: bumped GitHub Actions to their latest majors (`checkout` / `setup-python` /
  `upload-artifact` @v7; publish action stays `release/v1`) and configured bandit
  to skip documented false positives (`B105` env-var names / `Bearer` literal,
  `B608` parameterized SQL). The full pipeline (lint, type-check, tests 3.11/3.12,
  security scan) is green end-to-end.

## [0.3.1] - 2026-07-24

### Added

- Distribution: install-from-GitHub instructions (works before PyPI) and a manual
  `Publish to PyPI` GitHub workflow using Trusted Publishing (OIDC, no stored
  token); `docs/packaging.md` documents PyPI registration + setup.
- `JN-34`: remote MCP transport — `http_app` exposes the MCP server as a
  streamable-HTTP ASGI app, and a `jira-nano-mcp-http` console script serves it.

## [0.3.0] - 2026-07-24

### Added

- `JN-27`: packaging & distribution — `jira-nano` / `jira-nano-mcp` console scripts,
  optional extras (`mcp`/`http`/`telegram`), `docs/packaging.md` (install via
  `uv tool`/`pipx`, build, publish). **Phase 5 (Skill packaging) complete — all
  five phases done.**
- `JN-38`: CLI (`jira_nano.cli`, `jira-nano` console script) — `create`, `get`,
  `list`, `search` (JQL), `transition`, `assign`, `comment`, `board` over the
  service layer, no extra dependencies.
- `JN-26`: skill + MCP wiring — a `jira-nano-mcp` console entry point
  (`jira_nano.mcp_server:run`, stdio), a sample client config (`examples/mcp.json`),
  and an end-to-end agent-flow test (create → transition → comment → search).
- `JN-25`: `SKILL.md` — an Agent Skill (agentskills.io format) describing how to
  drive jira_nano via its MCP tools / CLI, with when-to-use triggers; validated by
  tests.
- `JN-37`: polling fallback (`jira_nano.githost.polling.poll_once`) — for hosts
  without webhooks, fetches + parses + dispatches events through the same
  pipeline, deduped by a `seen` set. **Phase 4 (Git-host) complete.**
- `JN-22`: GitHub integration (`jira_nano.githost.github.parse_github`) —
  symmetric to GitLab: normalizes pull-request (opened / merged / closed) and push
  payloads into `GitHostEvent`.
- `JN-21`: GitLab integration (`jira_nano.githost.gitlab.parse_gitlab`) —
  normalizes merge-request (open/merge/close) and push payloads into
  `GitHostEvent`; drives linking + transitions end-to-end via the receiver.
- `JN-36`: webhook receiver + normalized event model (`jira_nano.githost.webhook`)
  — a FastAPI listener (separate from the Jira REST API) that verifies GitLab
  (token) / GitHub (HMAC-SHA256) signatures, normalizes payloads into
  `GitHostEvent`, and dispatches them (link + transition).
- `JN-23`: link writer (`jira_nano.githost.links.link_ticket`) — appends a
  commit/MR/PR link to a ticket's `links[]`, idempotent on replay.
- `JN-24`: git-host event → transition (`jira_nano.githost.apply`) — advances a
  ticket forward along the shortest legal path to the event's target status
  (`JN-D1`), auto-assigning the MR/PR author to satisfy the `in-progress` guard;
  skips + notes if unreachable.
- `JN-20`: `JN-<n>` id parser (`jira_nano.githost.parser.find_ids`) — extracts
  ticket refs from commit messages / MR / PR titles / branches, deduped and
  order-preserving, with no false positives.
- `JN-19`: comment pull-back (`jira_nano.telegram.pullback`) — a human topic
  message is written back into the ticket as a comment (`source=telegram`, author
  resolved from the directory); wired into the bot's message handler.
  **Phase 3 (Telegram mirror) complete.**
- `JN-18`: update posts (`jira_nano.telegram.updates`) — `format_event` renders a
  change-feed event and `post_events` posts each into its ticket's topic, skipping
  Telegram-sourced comments to avoid echoes.
- `JN-16`: assignment pings (`jira_nano.telegram.pings`) — `ping_assignee` posts a
  `@mention` (Telegram handle from the user directory, `@handle` fallback) into the
  ticket's topic on assignment.
- `JN-17`: topic status icons — `topic_title` (status icon + 🚫 blocked overlay)
  and `topic_color` from the workflow (`JN-D1`); `refresh_topic` renames the forum
  topic to reflect the current state.
- `JN-35`: git change-feed (`jira_nano.changefeed`) — `diff_tickets` derives
  semantic events (created / status / assignee / blocked / comment / link) from
  two ticket states, and `changes_between` derives them from two commits.
- `JN-15`: forum topic management (`jira_nano.telegram.topics`) — `ensure_topic`
  creates one topic per ticket and persists the ticket↔topic mapping as a
  `telegram` `links[]` entry (reused thereafter); Telegram calls hidden behind a
  `TopicGateway`.
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
