# MCP tool surface

> **Status: DRAFT / proposal (`JN-D6`).** Specs the MCP tool shape (`JN-11`,
> `JN-12`) by copying common Jira MCP servers, scoped to a git-backed nano
> tracker. Open scoping questions at the bottom.

## Reference servers surveyed

| Server | Reach | Notes |
|--------|-------|-------|
| **Atlassian Rovo MCP** (official remote) | Jira, Confluence, JSM, Bitbucket, Compass | GA 2026-02-04; grouped by `read`/`write`/`search`; **no delete** (deliberate); Cloud-only; hosted; acts within the signed-in user's permissions. |
| **`sooperset/mcp-atlassian`** (community) | Jira + Confluence | ~63 Jira tools; Cloud **and** Server/DC; broadest surface (agile, JSM, forms, versions, worklogs, dev-info). The server connected in this session. |

## Design stance for `jira_nano`

1. **Keep tool names & arg shapes close to `mcp-atlassian`** so existing agent
   workflows are drop-in (`JN-12`).
2. **Scope to a git-backed nano tracker.** Map Jira features onto our model where
   they fit, and drop Cloud-/enterprise-only surfaces:
   - Git history **is** the changelog and dev-info panel.
   - `.jira_nano/users.yaml` **is** the user directory.
   - The configured workflow (`JN-D1`) **is** transitions.
3. **Follow the "create/update only, no hard delete" stance** of the official
   server (proposed — see open questions): closing = `archived`, and git history
   preserves everything anyway.

## Capability matrix

Legend: ✅ copy (keep Jira name) · 🔧 adapt onto our model · 🕒 defer (later phase) · ❌ drop (out of scope).

### Issues & CRUD

| Jira tool | jira_nano | Notes |
|-----------|:--------:|-------|
| `jira_create_issue` | ✅ | Core create → `tickets/JN-<n>.md`. |
| `jira_get_issue` | ✅ | Read one ticket. |
| `jira_update_issue` | ✅ | Edit frontmatter/body fields (incl. `blocked`, `priority`, `labels`, `parent`). |
| `jira_batch_create_issues` | ✅ | Bulk create — valuable for agents. |
| `jira_delete_issue` | 🔧 | Proposed: **no hard delete**; map to `archived` (open Q1). |
| `jira_batch_get_changelogs` | 🔧 | Serve from `git log` of the ticket file. |
| `jira_get_issue_dates` | 🔧 | From `created`/`updated` frontmatter. |
| `jira_get_create_fields`, `jira_get_field_options`, `jira_search_fields`, `jira_get_project_fields`, `jira_get_project_issue_types` | 🕒 | Schema is fixed (`JN-D3`); expose a minimal stub later for Jira-client compat. |

### Search / list / board

| Jira tool | jira_nano | Notes |
|-----------|:--------:|-------|
| `jira_search` (JQL) | ✅ | Cache-backed; a JQL-ish filter subset (status/assignee/label/priority/text). |
| `jira_get_project_issues` | ✅ | Filtered list. |
| `jira_get_board_issues` | 🔧 | Board view grouped by workflow status. |
| `jira_get_agile_boards` | 🔧 | One implicit board per repo (by status). |
| `jira_search_projects`, `jira_get_all_projects` | 🕒 | One project = one repo; stub for compat later. |
| `jira_get_project_components` | 🕒 | Components ≈ `labels` for now. |

### Transitions / status

| Jira tool | jira_nano | Notes |
|-----------|:--------:|-------|
| `jira_get_transitions` | ✅ | List legal transitions from current state (`JN-D1`). |
| `jira_transition_issue` | ✅ | Core; strictly validated, no force. |
| `jira_move_issue`, `jira_move_issues_to_backlog` | ❌ | Multi-project / backlog concepts we dropped. |

### Assignment & users

| Jira tool | jira_nano | Notes |
|-----------|:--------:|-------|
| `jira_assign_issue` | ✅ | Sets `assignee`; triggers Telegram ping. |
| `jira_search_assignable_users` | 🔧 | From `.jira_nano/users.yaml`. |
| `jira_get_user_profile` | 🔧 | From `.jira_nano/users.yaml`. |

### Comments

| Jira tool | jira_nano | Notes |
|-----------|:--------:|-------|
| `jira_add_comment` | ✅ | Appends an HTML-comment block (`JN-D3`). |
| `jira_edit_comment` | ✅ | Edits a block in place. |

### Watchers

| Jira tool | jira_nano | Notes |
|-----------|:--------:|-------|
| `jira_add_watcher`, `jira_remove_watcher`, `jira_get_issue_watchers` | ✅ | Maps to our `watchers[]`; drives extra Telegram pings. |

### Links & epics

| Jira tool | jira_nano | Notes |
|-----------|:--------:|-------|
| `jira_link_to_epic` | ✅ | Sets `parent` (epic). |
| `jira_get_project_epic_hierarchy` | ✅ | `parent` tree. |
| `jira_create_remote_issue_link` | 🔧 | Appends to `links[]` (commit/MR/PR/URL). |
| `jira_create_issue_link`, `jira_remove_issue_link`, `jira_get_link_types` | 🕒 | Generic issue-to-issue links (blocks/relates) beyond `parent` — later. |
| `jira_get_cross_project_dependencies` | ❌ | Single project. |

### Dev info (git integration)

| Jira tool | jira_nano | Notes |
|-----------|:--------:|-------|
| `jira_get_issue_development_info`, `jira_get_issues_development_info` | 🔧 | From `links[]` + git-host integration (Phase 4). On-brand. |

### Deferred / out of scope

| Jira area & tools | jira_nano | Notes |
|-------------------|:--------:|-------|
| Worklogs (`jira_add_worklog`, `jira_get_worklog`) | 🕒 | Time tracking — not in nano v1. |
| Agile/sprints (`jira_*_sprint*`, `jira_add_issues_to_sprint`) | 🕒 | Not sprint-based in v1. |
| Versions/releases (`jira_*_version*`) | 🕒 | Could map to labels/milestones later. |
| Attachments/images (`jira_download_attachments`, `jira_get_issue_images`) | 🕒 | Files-in-git story TBD. |
| Service Management (`jira_create_customer_request`, `jira_get_service_desk_*`, `jira_get_queue_issues`, `jira_get_request_type*`, `jira_get_issue_sla`) | ❌ | JSM — out of scope. |
| Proforma forms (`jira_get_issue_proforma_forms`, `jira_get_proforma_form_details`, `jira_update_proforma_form_answers`) | ❌ | Out of scope. |

## Proposed v1 tool set (curated)

Copy these first — they cover the architecture's eight operations plus the
Jira-shaped extras that map cleanly:

```
# CRUD
jira_create_issue        jira_get_issue          jira_update_issue
jira_batch_create_issues

# search / list / board
jira_search              jira_get_project_issues jira_get_board_issues

# workflow
jira_get_transitions     jira_transition_issue

# people
jira_assign_issue        jira_search_assignable_users  jira_get_user_profile

# comments
jira_add_comment         jira_edit_comment

# watchers
jira_add_watcher         jira_remove_watcher     jira_get_issue_watchers

# links / epics / dev
jira_link_to_epic        jira_get_project_epic_hierarchy
jira_create_remote_issue_link
jira_get_issue_development_info

# history
jira_batch_get_changelogs        # served from git log
```

`jira_nano`-specific capability not present in Jira: the **`blocked` impediment
flag** (`JN-D1`). Proposed to fold into `jira_update_issue` (set
`blocked`/`blocked_reason`) rather than add a bespoke tool.

## Open questions (`JN-D6`)

1. **Delete semantics.** Follow the official server (**no hard delete**, map
   `jira_delete_issue` → `archived`), or keep a real delete tool (git makes it
   recoverable)?
2. **Time tracking (worklogs).** Defer to v2, or include from the start?
3. **Agile & releases (sprints/versions).** Defer to v2, or scope some now?
4. **Attachments.** Defer, or design a files-in-git story now?
5. **Naming prefix.** Keep the `jira_` prefix verbatim for maximal drop-in
   compatibility, or use a `jn_`/`jira_nano_` namespace with aliases?
