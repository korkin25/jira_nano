# Features

> All features below are **planned**. Nothing is implemented yet — this
> repository is in the planning stage. Status legend: `[planned]`.

## Core: Git ticket store

1. `[planned]` One Markdown file per ticket at `tickets/JN-<n>.md`.
2. `[planned]` YAML frontmatter schema: `id`, `title`, `status`, `assignee`,
   `labels`, `priority`, `created`, `updated`, `links`; Markdown body for
   description and comments.
3. `[planned]` Git history as the audit trail — every change is a commit
   referencing the ticket id.
4. `[planned]` Sequential ticket ids under the `JN-<n>` scheme, never reused.

## Core: SQLite query cache

5. `[planned]` Rebuildable SQLite cache indexing ticket frontmatter for fast
   queries.
6. `[planned]` Full rebuild from `tickets/*.md` on demand or after external Git
   changes.
7. `[planned]` Incremental upsert of a single ticket after a local write.
8. `[planned]` Cache is never authoritative and is excluded from Git.

## Core: CRUD & search

9. `[planned]` Create, read, update tickets through a shared service layer.
10. `[planned]` Full-text and field search served by the cache.
11. `[planned]` List with filters (status, assignee, label, priority).
12. `[planned]` Board view grouped by workflow status.

## Workflow / status model

13. `[planned]` Configurable workflow — states plus allowed transitions in a
    config file.
14. `[planned]` Transition validation in the API layer for every mutating
    operation.
15. `[planned]` Terminal states archive/close a ticket.
16. `[planned]` Status mirrored to Telegram icons (see draft in
    `docs/status-model.md`).

## MCP server + HTTP API

17. `[planned]` MCP server exposing `create` / `update` / `transition` /
    `assign` / `comment` / `search` / `list` / `board`.
18. `[planned]` Tool shape close to common Jira MCP servers for drop-in AI
    workflows.
19. `[planned]` HTTP API exposing the same operations for non-MCP clients.

## Telegram bot mirror

20. `[planned]` Telegram **Bot API** integration (multi-user, ToS-clean,
    webhooks) — not a userbot.
21. `[planned]` Forum topic/thread management: a thread per ticket (or epic).
22. `[planned]` Assignment pings that `@mention` the assignee.
23. `[planned]` Status reflected via topic/message icons.
24. `[planned]` Ticket updates posted as messages into the ticket thread.
25. `[planned]` Pull human comments written in Telegram back into ticket files.

## Git-host integration

26. `[planned]` Parse `JN-<n>` ids in commit messages and MR/PR titles.
27. `[planned]` Support **both GitLab and GitHub** symmetrically.
28. `[planned]` Link commits and MRs/PRs into ticket frontmatter `links`.
29. `[planned]` Advance ticket status on Git-host events.
30. `[planned]` Webhook-driven with polling fallback.

## Agent Skill packaging

31. `[planned]` Ship as an Agent Skill (`SKILL.md`) targeting the Agent Skills
    (agentskills.io) standard.
32. `[planned]` Skill + MCP so agents (OpenClaw / Claude / others) can manage
    tickets natively.
