# HTTP API (Jira REST compatibility)

> **Status: RESOLVED (`JN-D5`).** Specs the HTTP API as a **drop-in Jira REST
> surface**. It is a thin adapter over the shared service layer (`JN-D4`) and
> mirrors the MCP tool surface (`JN-D6`); one service layer validates the
> workflow (`JN-D1`) for both front doors.

## Goal

Existing Jira clients and SDKs should work unmodified. Internal storage is
git-backed Markdown (`JN-D3`); the API presents it in Jira's JSON envelope.

## Dialects served: **both v2 and v3**

Both base paths are served, plus the `latest` alias:

| Base path | Dialect | Text bodies | Users | Search |
|-----------|---------|-------------|-------|--------|
| `/rest/api/2/…` | Server / Data Center | **plain string** | `name` / `key` (username) | classic `/search?jql=`, `startAt`/`total` |
| `/rest/api/3/…` | Cloud | **ADF** (nested JSON) | `accountId` | `/search/jql`, `nextPageToken` |
| `/rest/api/latest/…` | alias → **v3** | — | — | — |

Serving both is more work (ADF conversion + dual identity model) but maximizes
drop-in compatibility.

## Text bodies: Markdown ↔ dialect

Internally, `description` and comment bodies are Markdown.

- **v2:** emitted/accepted as a **plain string** (Markdown passes through).
- **v3:** converted to/from **ADF** (Atlassian Document Format). A Markdown↔ADF
  converter maps the common nodes (headings, lists, code, links, emphasis);
  unsupported nodes degrade gracefully to text. Exact node coverage is finalized
  in `JN-13`.

## Identities

- **v2:** the user object exposes `name` and `key` = the canonical handle
  (`.jira_nano/users.yaml`).
- **v3:** the user object exposes `accountId`, derived from the handle and
  overridable via an optional `account_id` in `users.yaml`. `displayName` /
  `emailAddress` come from the directory too.

## Endpoint set (mirrors `JN-D6`)

Under `/rest/api/{2,3}/`:

| Method & path | Operation |
|---------------|-----------|
| `GET /issue/{key}` | Get a ticket |
| `POST /issue` | Create |
| `PUT /issue/{key}` | Update |
| `DELETE /issue/{key}` | **Maps to `archived`** (no hard delete — `JN-D6`) |
| `GET /issue/{key}/transitions` | List legal transitions (`JN-D1`) |
| `POST /issue/{key}/transitions` | Transition (strict, no force) |
| `PUT /issue/{key}/assignee` | Assign (triggers Telegram ping) |
| `GET/POST /issue/{key}/comment`, `GET/PUT/DELETE /issue/{key}/comment/{id}` | Comments |
| `GET/POST/DELETE /issue/{key}/watchers` | Watchers |
| `GET/POST /issue/{key}/remotelink` | Remote links → `links[]` |
| `GET/POST /search` (v2) · `POST /search/jql` (v3) | Search (JQL subset) |
| `GET /issue/createmeta`, `GET /issue/{key}/editmeta` | Field metadata (fixed-schema stub) |
| `GET /status`, `/priority`, `/issuetype`, `/field` | Enumerations (our fixed sets) |
| `GET /project`, `/project/{key}` | Project (one project = the repo) |
| `GET /myself`, `/user` | Users (from the directory) |

Out-of-scope Jira areas (JSM, `/rest/agile/…`, worklogs, versions, attachments)
return `404`/empty, consistent with `JN-D6`.

## Search & JQL

- **JQL subset:** fields `status`, `assignee`, `reporter`, `labels`, `priority`,
  `type` (`issuetype`), `parent`, and free text (`~`); operators `=`, `!=`,
  `IN`, `~`, `AND`, `OR`; plus `ORDER BY`. Extensible later.
- **v2 response:** `{ startAt, maxResults, total, issues: [...] }`.
- **v3 response:** `{ nextPageToken, isLast, issues: [...] }` (token pagination,
  no `total`) — per the current `/search/jql` contract.

## Field mapping (`jira_nano` → `issue.fields`)

| Jira field | jira_nano source |
|------------|------------------|
| `summary` | `title` |
| `description` | body `## Description` (string v2 / ADF v3) |
| `issuetype` | `type` (task/bug/epic) |
| `status` + `statusCategory` | `status` → category: `todo`=**To Do**, `in-progress`/`in-review`=**In Progress**, `done`/`archived`=**Done** |
| `priority` | `priority` (low/medium/high/urgent) |
| `assignee` | `assignee` (`name` v2 / `accountId` v3) |
| `reporter` | `reporter` |
| `labels` | `labels` |
| `parent` | `parent` |
| `resolution` | `resolution` (on `archived`) |
| `Flagged` (customfield) | `blocked` → value `Impediment`; `blocked_reason` in an adjacent custom field |
| `comment` | `## Comments` blocks |
| `issuelinks` / `remotelinks` | `links[]` |
| `created` / `updated` | `created` / `updated` |

## Authentication

All three schemes (secrets from env/config, never in git):

- **Basic** — `username:token`.
- **Bearer PAT** — personal access tokens.
- **OAuth 2.0** — accept/validate OAuth 2.0 access tokens. `jira_nano` acts as
  its own OAuth 2.0 provider (authorization-code + client-credentials grants);
  validating tokens from an external issuer is an option. The exact grant/issuer
  setup is finalized in `JN-13`.

## Errors

Jira error envelope: `{ "errorMessages": [...], "errors": { ... } }` with the
matching HTTP status.

## Open implementation notes (for `JN-13`)

- Markdown↔ADF node coverage.
- OAuth 2.0 grant types and provider-vs-external-issuer setup.
