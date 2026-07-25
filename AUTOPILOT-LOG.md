# Autopilot log — jira_nano

Autonomous changes (user authorized full autopilot on these repos). Newest first.

## 2026-07-26 — JN-51: adopt the ai-project-template standard

- **CI is now a composition of `korkin25/open-ci-actions@v1`** (`detect` → `version` →
  `python` / `sast` / `docker` / `helm` / `functional`), replacing the previous inline jobs,
  plus one bespoke `quality` job that keeps the **JN-47 xenon complexity HARD gate**
  (`auto-tests/group-a/complexity-gate.sh`) — the shared python job's xenon is a soft trend
  signal only. _Reverse:_ restore the previous inline `ci.yml` from git history.
- **GitVersion** added (`GitVersion.yml`, branch model `feature/*` → `dev` → `rc` → `release`);
  versions are auto-generated, never hardcoded.
- **Branch model migrated** `main` → `dev`/`rc`/`release`. `dev` is the default branch; `main`
  is kept only as legacy history.
- **Functional test converted to the script-driven model.** The old inline HTTP-API e2e job is
  now `auto-tests/group-a/validate-deploy.sh`: build the image, boot `jira-nano-http`, and probe
  `GET /rest/api/2/myself` with a bearer token (self-contained default token — no CI secret).
  Contract exit 0/77/other; probe host portable across GitHub and GitLab DinD (`DOCKER_HOST`).
  The functional runner's glob is `validate-*.sh` so it does not also run `complexity-gate.sh`.
  Helm lint/template moved to the shared `helm` job.
- **PyPI publishing stays in the vendored `publish.yml`** (manual `workflow_dispatch`); the
  reusable release workflow can't trusted-publish cross-repository (PyPI `job_workflow_ref`
  limitation), so there is no `release` job in `ci.yml`.
- **Universal agent-rule pickup.** `CLAUDE.md` is the single source; `AGENTS.md`, `GEMINI.md`,
  `.cursorrules`, `.clinerules`, `.windsurfrules`, `.github/copilot-instructions.md` are
  symlinks to it, and `.cursor/rules/project.mdc` is a thin pointer. The old `AGENTS.md`
  pointer's unique note (Agent-Skills target) was folded into `CLAUDE.md`.
- **CLAUDE.md hardened** with the template's universal sections: "Start here — context map"
  router, "Versioning", "Safe autonomy", "Agent security working agreements", "Design before
  code", and a per-turn hook (`.claude/settings.json`) that re-injects the context map.
- **Doc-sync guard** (`.github/workflows/doc-sync.yml`), **Dependabot**, **pre-commit**
  (gitleaks via Docker only), **CODEOWNERS**, PR/issue templates, `SECURITY.md`,
  `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, and a `.gitlab-ci.yml` mirror (using
  `open_ci_cd/templates`) were added.

**Guardrails honored:** feature branch `feature/JN-51-full-standard` off `dev`; no history
rewrite; no secret touched; License stays GPL-3.0-or-later.
