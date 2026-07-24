# Test plan

Per-feature test catalog for `jira_nano`. When a feature is picked up for
implementation, add a section here listing its concrete tests **before** writing code
(see the Testing policy in [../CLAUDE.md](../CLAUDE.md)). Each test is tagged by group:

- **(a) Fully automated** — runs in GitHub Actions CI on every push/PR. Scripts live in
  [../auto-tests/](../auto-tests/) and are wired into CI. Claude analyses the run logs
  even when green.
- **(b) Dev-machine / AI-sandbox** — runnable only against external services (live
  Telegram bot, GitLab/GitHub webhooks, MCP/HTTP server end-to-end) or not fully
  automatable; run in an isolated sandbox under Claude's control, opt-in via
  `JIRA_NANO_LIVE=1`.
- **(c) Human-in-the-loop** — needs a human; Claude writes a methodology and hands it over.

Per-test pass/fail status for the **current** feature is tracked in
[../TODO.md](../TODO.md); a feature is done only when 100% of its tests pass (group-(c)
methodology proposed).

---

## Baseline (delivered features 1–36)

The shipped suite (`pytest`, ruff + mypy clean) plus the gated live tests
(`JIRA_NANO_LIVE=1`) already cover the delivered features. New feature sections are
appended below as work is picked up.

<!-- Template — copy per new feature:

## Feature <n> — <title>

| Test | Group | What it asserts | Status |
|------|-------|-----------------|--------|
| ... | (a) | ... | ⬜ |
| ... | (b) | ... | ⬜ |
| ... | (c) | ... | ⬜ |
-->
