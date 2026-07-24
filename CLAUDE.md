# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) and any other AI
agent working in this repository. It is the **canonical rules file** for the
project.

## What this project is

`jira_nano` is a lightweight, AI-native issue tracker. The **source of record is
a plain Git repository**: every ticket is a versioned file
(`tickets/JN-<n>.md`) with YAML frontmatter plus a Markdown body, so the Git
history itself is the audit trail. A local **SQLite database is only a
rebuildable query cache** (indexes for fast search, filters and boards) — never
the source of truth.

Around that core, `jira_nano` adds three integration surfaces: a **Telegram bot
mirror** that replaces Jira-style email notifications (assignment pings, status
icons, ticket updates, and pulling human comments written in Telegram back into
the ticket files); an **MCP server + HTTP API** whose tool shape is deliberately
close to common Jira MCP servers so existing AI workflows are drop-in; and
**Git-host integration** that links commits and MRs/PRs to tickets across both
GitLab and GitHub. It is also shipped as an **Agent Skill** (`SKILL.md`) so
agents can manage tickets natively. Status: **released** — versions live in
`CHANGELOG.md`, open work in `TODO.md`, the feature backlog in `Features.md`.

## Language rules (STRICT)

- **All repository content is English** — code, identifiers, comments, docstrings,
  commit messages, and every document (README, `docs/`, CHANGELOG, TODO, this file).
  No exceptions.
- **Conversation with the user is always Russian** — reply in Russian regardless of
  the language they wrote in. This applies only to the live chat, never to anything
  written into the repo.

## Feature backlog — `Features.md` (root)

- Everything the user asks to build, and every "add for brainstorm" idea, is a
  **numbered** entry in `Features.md` at the repository **root** (never under
  `docs/`). If a features doc lives under `docs/`, move it to the root.
- Numbers are **stable and never reused**. Entries are grouped by state:
  **Current** (in progress) · **Planned** · **Brainstorm** (ideas) · **Delivered**.
- A new idea from the user lands here first (as Brainstorm or Planned) before it
  becomes a task in `TODO.md`.

## Documentation sync (apply without being asked)

Keep docs in lockstep with the code, **in the same change** — never wait to be asked:

| What changed | Update |
|---|---|
| New/changed feature or behavior | `Features.md` (root) entry + `README.md` |
| CLI / API / MCP surface (commands, flags, tools) | `README.md` + relevant `docs/*.md` |
| Architecture, storage schema, data flow, security model | `docs/architecture.md` |
| A feature is picked up for implementation | its test section in `docs/tests.md` |
| Any user-visible change | `CHANGELOG.md` under `## [Unreleased]` |
| Task started / finished / blocked, or a test's pass status | `TODO.md` |
| User asks to build something, or "add for brainstorm" | numbered entry in `Features.md` |

- `CHANGELOG.md` follows [Keep a Changelog](https://keepachangelog.com/) + SemVer.
- `TODO.md` holds only open/in-progress work and the per-test pass status of the
  current feature; a done+verified task moves to `CHANGELOG.md` in the same change.
- Never mark a task done without proof it works — see **Testing policy**.

## Testing policy (apply without being asked)

**Three test groups:**

- **(a) Fully automated** — unit/integration tests plus all debugging. Run in
  GitHub Actions CI on every push/PR. Claude **must read and analyze the CI run
  logs** (`gh run view --log`) for every run — **even when the job is green**.
- **(b) Dev-machine / AI-sandbox** — tests runnable only on a developer machine or
  against external services (live Telegram bot, GitLab/GitHub webhooks, the MCP /
  HTTP server end-to-end) or not fully automatable, run in an **isolated sandbox
  under Claude's control** — opt-in via `JIRA_NANO_LIVE=1`. Claude runs these
  itself during development, and again after a release once full CI is green.
- **(c) Human-in-the-loop** — require a human. Claude writes a **methodology** and
  proposes it to the user to run.

**TDD & flow:**

- For every feature/bug write the automated tests **FIRST** (they must fail), then
  implement until green. No feature code without a test.
- A task is **done only when 100% of its features are tested** — every applicable
  group covered, group-(c) methodology proposed.
- **Do not start a new feature until the current one is fully tested.**

**Artifacts & structure:**

- When a feature is picked up, immediately add a section to `docs/tests.md` listing
  its concrete tests, each tagged `(a)`/`(b)`/`(c)`.
- All test scripts, scenarios, and methodologies (**every group**) live structured
  under `auto-tests/`. Group-(a) is wired into CI to run automatically. Every
  scenario/methodology is also **used during development**, not only in CI.
- `TODO.md` tracks the pass/fail status of each test of the current feature.

**Release gate:**

- Group-(a) must be **green in CI** to release. If CI fails → **no release**; keep
  fixing until CI is green.
- After a release (full CI green) Claude re-runs group-(b); any remaining group-(c)
  tests → methodology handed to the user.

## Development workflow (autonomous — apply without being asked)

This project is developed by an AI agent under continuous, autonomous iteration.

- Test-driven: for every agreed feature write the tests FIRST (they must fail), then implement until green. No feature code without a test.
- Feature branches: work on feature/<task-id>-<slug> off main; merge to main only when the full suite is green.
- Commit periodically in small logical units, Conventional Commits (feat:, fix:, test:, docs:, chore:, ci:). Never add a Co-Authored-By trailer. Push to `origin` after every commit.
- Releases only after green tests: tag vX.Y.Z (SemVer) after the full suite passes on main. Publishing to PyPI or marketplaces is a separate, later, explicit step.
- CI on every push (GitHub Actions): ruff lint, pytest (3.11 and 3.12), security scan (bandit + pip-audit). A tag triggers the build/release job.
- Security first: no secrets in git; least privilege; treat the Telethon session / bot token as full-access credentials.
- High bar: type hints, docstrings, ruff-clean, meaningful tests. Work like a top-tier engineer + DevOps.
- Auto-logging: started/ongoing work goes to TODO.md (Current state + phase tables); completed and verified work moves to CHANGELOG.md, in the same change. Never mark a task done without a passing test.
- Cold-start: keep the top of TODO.md a "Current state / next action" block so a fresh session knows exactly what to do next.

### Per-task lifecycle (MANDATORY — in this order)

1. **Log first.** The task exists in `TODO.md` as `JN-<n>` before any work begins. If it is not logged, log it first.
2. **Backlog.** Ensure the feature is a numbered entry in root `Features.md`.
3. **Test plan.** Add the feature's section to `docs/tests.md` (groups a/b/c).
4. **Branch.** Create `feature/JN-<n>-<slug>` off `main`.
5. **TDD.** Write the failing group-(a) test(s) first; implement until green; commit in small logical units on the branch and push after each.
6. **Verify.** Group-(a) green in CI (analyze the run logs even when green); run group-(b) in dev/sandbox (`JIRA_NANO_LIVE=1`); update each test's status in `TODO.md`.
7. **Record.** When done and the full suite is green, move the item from `TODO.md` to `CHANGELOG.md`.
8. **MR.** Open an MR/PR to `main`; merge with `--no-ff` only when CI is green, then push `main`.

## Conventions

- **Git is the source of record.** Ticket files under `tickets/` are the
  authoritative state; treat their Git history as the audit log.
- **The SQLite cache is derived and rebuildable.** It must be reconstructable
  from the ticket files at any time and must never be committed or trusted as
  primary state.
- **Secrets never go in git.** No tokens, sessions, or credentials in the repo —
  see `.gitignore`. Configuration containing secrets is loaded from the
  environment or from ignored local files only.
- **The bot token is a credential.** The Telegram Bot API token (and any
  Telethon session file) grants full access to the bot's identity; handle it
  with the same care as a private key and revoke on any suspected leak.
- **Ticket ids use the `JN-<n>` scheme.** Internal work items and decisions are
  tracked in `TODO.md` (`JN-<n>` for tasks, `JN-D<n>` for decisions); numbers
  are mandatory, sequential, and never reused.
- **License is GPL-3.0.** All contributions are under GPL-3.0-or-later.
