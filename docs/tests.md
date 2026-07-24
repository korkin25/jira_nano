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

## Feature 45–49 — Container image + Helm chart + GHCR CI (JN-46)

| Test | Group | What it asserts | Status |
|------|-------|-----------------|--------|
| `helm lint chart` | (a) | chart lints clean | ✅ |
| `helm template` (default + toggles) | (a) | renders for all value permutations | ✅ |
| `docker build .` | (a) | image builds; app importable; entrypoint present | ✅ |
| `auto-tests/group-a/validate-deploy.sh` | (a) | CI-runnable: helm lint+template + docker build | ✅ |
| Image runs `jira-nano-http`, serves :8080 | (b) | container boots, TCP :8080 accepts | ⬜ |
| `helm install` on a kind cluster; init + probes | (b) | StatefulSet ready, PVC bound, init idempotent | ⬜ |
| Voice model fetched to the PVC on first STT | (b) | model lands on `/models`, survives restart | ⬜ |
| GHCR image + OCI chart pull post-release | (c) | manual: `docker pull` / `helm pull` after a tag | ⬜ |

Group-(b) methodology: `auto-tests/group-b/kind-deploy.md`.

## Feature 50 — Xenon complexity hard gate (JN-47)

| Test | Group | What it asserts | Status |
|------|-------|-----------------|--------|
| `auto-tests/group-a/complexity-gate.sh` | (a) | `xenon --max-absolute C --max-modules B --max-average A src` exits 0 (no module ranks C+) | ✅ |
| CI `quality` job (hard) | (a) | the gate is no longer `continue-on-error`; a regression fails the build | ✅ |
| `pytest tests/test_githost_github.py tests/test_githost_gitlab.py` | (a) | parser behavior unchanged after the refactor | ✅ |

<!-- Template — copy per new feature:

## Feature <n> — <title>

| Test | Group | What it asserts | Status |
|------|-------|-----------------|--------|
| ... | (a) | ... | ⬜ |
| ... | (b) | ... | ⬜ |
| ... | (c) | ... | ⬜ |
-->
