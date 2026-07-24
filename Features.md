# Features

The single **numbered backlog** for `jira_nano`: everything the user asks to build and
every brainstorm idea. Numbers are **stable and never reused**. Entries are grouped by
state — **Current** (in progress) · **Planned** · **Brainstorm** (ideas) · **Delivered**.
New requests and ideas land here first, then become tasks in [TODO.md](TODO.md).

## Current (in progress)

_None._

## Planned

37. **Worklogs / time tracking.** Deferred to v2 (`JN-D6`).
38. **Sprints & agile boards.** Deferred to v2 (`JN-D6`).
39. **Versions / releases.** Deferred to v2 (`JN-D6`).
40. **Attachments.** Files-in-git story, deferred to v2 (`JN-D6`).
41. **Jira-compat field metadata.** `createmeta` / `editmeta`, projects/components, and
    generic issue links (blocks/relates) beyond `parent` — currently minimal/absent.
42. **OAuth 2.0 authorization-code flow.** Only `client_credentials` is implemented;
    plus fuller Markdown↔ADF node coverage (common nodes only today).
43. **Single-file build.** PyInstaller/shiv — evaluated, not built (`JN-D2`).

## Brainstorm (ideas)

44. **JSM / service desk surface** — service-desk, proforma forms, SLA, and the other
    Atlassian products (out of scope for now, `JN-D6`).

## Delivered

### Core: Git ticket store

1. One Markdown file per ticket at `tickets/JN-<n>.md`.
2. YAML frontmatter schema: `id`, `title`, `status`, `assignee`, `labels`, `priority`,
   `created`, `updated`, `links`; Markdown body for description and comments.
3. Git history as the audit trail — every change is a commit referencing the ticket id.
4. Sequential ticket ids under the `JN-<n>` scheme, never reused.

### Core: SQLite query cache

5. Rebuildable SQLite cache indexing ticket frontmatter for fast queries.
6. Full rebuild from `tickets/*.md` on demand or after external Git changes.
7. Incremental upsert of a single ticket after a local write.
8. Cache is never authoritative and is excluded from Git.

### Core: CRUD & search

9. Create, read, update tickets through a shared service layer.
10. Full-text and field search served by the cache.
11. List with filters (status, assignee, label, priority).
12. Board view grouped by workflow status.

### Workflow / status model

13. Configurable workflow — states plus allowed transitions in a config file.
14. Transition validation in the API layer for every mutating operation.
15. Terminal states archive/close a ticket.
16. Status mirrored to Telegram icons (see `docs/status-model.md`).

### MCP server + HTTP API

17. MCP server exposing `create` / `update` / `transition` / `assign` / `comment` /
    `search` / `list` / `board`.
18. Tool shape close to common Jira MCP servers for drop-in AI workflows.
19. HTTP API exposing the same operations for non-MCP clients (drop-in Jira REST v2+v3).

### Telegram bot mirror

20. Telegram **Bot API** integration (multi-user, ToS-clean, webhooks) — not a userbot.
21. Forum topic/thread management: a thread per ticket (or epic).
22. Assignment pings that `@mention` the assignee.
23. Status reflected via topic/message icons.
24. Ticket updates posted as messages into the ticket thread.
25. Pull human comments written in Telegram back into ticket files.

### Git-host integration

26. Parse `JN-<n>` ids in commit messages and MR/PR titles.
27. Support **both GitLab and GitHub** symmetrically.
28. Link commits and MRs/PRs into ticket frontmatter `links`.
29. Advance ticket status on Git-host events.
30. Webhook-driven with polling fallback.

### Agent Skill packaging

31. Ship as an Agent Skill (`SKILL.md`) targeting the Agent Skills (agentskills.io) standard.
32. Skill + MCP so agents (OpenClaw / Claude / others) can manage tickets natively.

### Post-1.0 polish

33. Telegram message design overhaul (monospace id, circle status palette, `<blockquote>`
    ticket/board views).
34. Telegram **auto-trigger**: change-feed → mirror on a background poller.
35. Static per-status **banners** sent as photo + caption (package assets, no runtime render).
36. **Voice-message transcription**: a voice reply in a ticket topic is transcribed
    (pluggable STT — local Whisper by default, optional OpenAI cloud) and pulled back into
    the ticket as a comment; the model is provisioned at startup, cached on disk.

### Deployment & CI (JN-46)

45. **Container image** — multi-stage `Dockerfile` (non-root uid 10000), default command
    serves the HTTP Jira REST API on :8080; published to `ghcr.io/korkin25/jira-nano`.
46. **Helm chart** (`chart/`) — StatefulSet + PVC for the git ticket store & SQLite cache,
    initContainer runs `jira-nano init`, TCP probes, optional Service/Ingress/ServiceMonitor/
    HPA/PDB; published as an OCI chart to `ghcr.io/korkin25/charts/jira-nano`.
47. **Voice-model PVC** — Whisper model kept off the image, on a chart PVC (fetched on first
    use or preloaded by devops); documented in `chart/README.md`. Identical pattern in tg_notes.
48. **`docker-compose.yml`** — local stack (init + HTTP API + optional bot/mcp-http profiles).
49. **CI security & quality suite** — checkov, hadolint, trivy, semgrep, radon/xenon added
    to the GitHub Actions pipeline; image + chart pushed to GHCR on main/tags.
