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
agents can manage tickets natively. The project is currently in the **planning**
stage — see `TODO.md` for the next action.

## Language rules (STRICT)

- **All repository content is English** — code, identifiers, comments, docstrings,
  commit messages, and every document (README, `docs/`, CHANGELOG, TODO, this file).
  No exceptions.
- **Conversation with the user is always Russian** — reply in Russian regardless of
  the language they wrote in. This applies only to the live chat, never to anything
  written into the repo.

## Development workflow (autonomous — apply without being asked)

This project is developed by an AI agent under continuous, autonomous iteration.

- Test-driven: for every agreed feature write the tests FIRST (they must fail), then implement until green. No feature code without a test.
- Feature branches: work on feature/<task-id>-<slug> off main; merge to main only when the full suite is green.
- Commit periodically in small logical units, Conventional Commits (feat:, fix:, test:, docs:, chore:, ci:). Never add a Co-Authored-By trailer.
- Releases only after green tests: tag vX.Y.Z (SemVer) after the full suite passes on main. Publishing to PyPI or marketplaces is a separate, later, explicit step.
- CI on every push (GitHub Actions): ruff lint, pytest (3.11 and 3.12), security scan (bandit + pip-audit). A tag triggers the build/release job.
- Security first: no secrets in git; least privilege; treat the Telethon session / bot token as full-access credentials.
- High bar: type hints, docstrings, ruff-clean, meaningful tests. Work like a top-tier engineer + DevOps.
- Auto-logging: started/ongoing work goes to TODO.md (Current state + phase tables); completed and verified work moves to CHANGELOG.md, in the same change. Never mark a task done without a passing test.
- Cold-start: keep the top of TODO.md a "Current state / next action" block so a fresh session knows exactly what to do next.

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
