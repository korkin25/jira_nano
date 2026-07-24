# jira_nano — install & setup guide

A hands-on walkthrough: install the tool, create a ticket repo, and wire up each
surface (CLI, MCP, HTTP Jira REST API, Telegram mirror, GitLab/GitHub webhooks).
Do the steps in order; each surface is independent, so stop whenever you have what
you need.

> **Conventions.** `<repo>` is the directory holding your tickets. Every surface
> points at it via the `JIRA_NANO_REPO` env var (or `--repo` for the CLI).
> Secrets go in the environment, never in Git.

---

## 1. Prerequisites

- **Python 3.11 or 3.12**
- **git** on your PATH
- **[pipx](https://pipx.pypa.io/stable/installation/)** (recommended installer)

```bash
python3 --version        # 3.11+ 
git --version
pipx --version
```

## 2. Install

```bash
pipx install "jira-nano[mcp,http,telegram]"   # >= 0.4.0 for `init` + run entrypoints
```

Extras are optional — install only what you need: `mcp` (MCP server), `http`
(HTTP API), `telegram` (bot). The CLI works with no extras. To run unreleased
changes, install from git:
`pipx install "jira-nano[...] @ git+https://github.com/korkin25/jira_nano.git"`.

Verify:

```bash
jira-nano --help
```

You should have these commands on your PATH: `jira-nano`, `jira-nano-mcp`,
`jira-nano-mcp-http`, `jira-nano-http`, `jira-nano-bot`, `jira-nano-webhooks`.

## 3. Create a ticket repository

```bash
mkdir ~/tickets && cd ~/tickets
jira-nano --repo . init
export JIRA_NANO_REPO="$PWD"      # so every surface finds the repo
```

`init` runs `git init` and writes `.jira_nano/workflow.yaml` (the default
workflow) and `.jira_nano/users.yaml` (a template). Git is the source of truth —
every change is a commit.

Smoke test the CLI:

```bash
jira-nano create --title "First ticket" --reporter me
jira-nano list
jira-nano board
jira-nano transition JN-1 in-progress   # (needs an assignee first — see below)
```

> **Workflow:** `todo → in-progress → in-review → done`, plus `archived`.
> Transitions are strict. `in-progress` requires an assignee, so:
> `jira-nano assign JN-1 me && jira-nano transition JN-1 in-progress`.

## 4. The user directory (needed for Telegram & git-host)

Edit `.jira_nano/users.yaml` to map your **canonical handles** to platform
identities. This is how the bot resolves who to `@mention` and how git-host
events match authors:

```yaml
me:
  name: "Your Name"
  telegram: "@your_tg_username"
  gitlab: your_gitlab_username
  github: your_github_username
  email: you@example.com
```

Commit it (`git add .jira_nano/users.yaml && git commit -m "add users"`).

## 5. MCP server (for AI agents)

Run over stdio and register it in your MCP client (Claude Desktop/Code, Cursor,
…). A sample config is in [`examples/mcp.json`](../examples/mcp.json):

```json
{
  "mcpServers": {
    "jira_nano": {
      "command": "jira-nano-mcp",
      "env": { "JIRA_NANO_REPO": "/home/you/tickets" }
    }
  }
}
```

Tools are Jira-named (`jira_create_issue`, `jira_search`, `jira_transition_issue`,
…) and return Jira issue JSON. For a remote MCP endpoint use `jira-nano-mcp-http`.

## 6. HTTP API (drop-in Jira REST)

Configure credentials and run the server:

```bash
export JIRA_NANO_TOKENS="alice:s3cret,bob:hunter2"      # username:token pairs
export JIRA_NANO_OAUTH_CLIENTS="ci-bot:clientsecret"     # optional OAuth2 clients
export JIRA_NANO_HTTP_HOST=127.0.0.1                     # default
export JIRA_NANO_HTTP_PORT=8080                          # default
jira-nano-http
```

Call it like Jira (both `/rest/api/2/…` and `/rest/api/3/…`, plus `latest`):

```bash
# Basic auth (username:token) or Bearer token:
curl -u alice:s3cret http://127.0.0.1:8080/rest/api/2/issue/JN-1
curl -H "Authorization: Bearer s3cret" \
     -X POST http://127.0.0.1:8080/rest/api/2/issue \
     -H "Content-Type: application/json" \
     -d '{"fields": {"summary": "From the API"}}'
# JQL search:
curl -u alice:s3cret "http://127.0.0.1:8080/rest/api/2/search?jql=status%20%3D%20todo"
# OAuth2 client-credentials -> bearer token:
curl -X POST http://127.0.0.1:8080/oauth/token \
     -d '{"grant_type":"client_credentials","client_id":"ci-bot","client_secret":"clientsecret"}'
```

## 7. Telegram bot mirror

**7.1 Create the bot.** Message [@BotFather](https://t.me/BotFather) → `/newbot`
→ follow the prompts → copy the **bot token**.

**7.2 Create a forum supergroup.**
- Create a group, open its settings, enable **Topics** (this makes it a forum).
- Add your bot to the group and make it an **admin** with **Manage Topics** and
  **Send Messages** permissions.

**7.3 Get the chat id.** Add [@RawDataBot](https://t.me/RawDataBot) (or
[@myidbot](https://t.me/myidbot)) to the group; it reports the supergroup id — a
negative number like `-1001234567890`.

**7.4 Run the bot:**

```bash
export TELEGRAM_BOT_TOKEN="123456:ABC-your-token"
export TELEGRAM_CHAT_ID="-1001234567890"
jira-nano-bot
```

Now assigning/transitioning a ticket posts to its forum topic and `@mention`s the
assignee; replies you type in a ticket's topic are pulled back into the ticket as
comments (committed to Git).

## 8. Git-host integration (GitLab / GitHub)

**8.1 Run the receiver** (it must be reachable from the git host):

```bash
export GITLAB_WEBHOOK_SECRET="pick-a-long-random-string"
export GITHUB_WEBHOOK_SECRET="another-random-string"
export JIRA_NANO_WEBHOOK_HOST=0.0.0.0    # bind for external access
export JIRA_NANO_WEBHOOK_PORT=8081
jira-nano-webhooks
```

For a public URL while testing, tunnel it (e.g. `ngrok http 8081` or
`cloudflared tunnel --url http://localhost:8081`) and use the resulting
`https://…` URL below.

**8.2 GitLab.** Project → *Settings → Webhooks* → URL
`https://<public>/webhooks/gitlab`, **Secret token** = `GITLAB_WEBHOOK_SECRET`,
triggers: *Push events* and *Merge request events*.

**8.3 GitHub.** Repo → *Settings → Webhooks → Add webhook* → Payload URL
`https://<public>/webhooks/github`, Content type `application/json`,
**Secret** = `GITHUB_WEBHOOK_SECRET`, events: *Pushes* and *Pull requests*.

Put a ticket id in the MR/PR title or a commit message (e.g. `JN-1: fix login`).
Opening the MR/PR moves `JN-1` to `in-review` (auto-advancing along the workflow
and auto-assigning the author), merging moves it to `done`, and the MR/PR is
linked in the ticket's `links[]`.

## 9. Notes & limits

- **Reads are served from the local cache**, which self-heals from Git — safe to
  `git pull` in `<repo>`; the tracker picks up external changes.
- **Not yet supported (by design):** worklogs/time-tracking, sprints/agile,
  versions/releases, attachments; JSM/service-desk and proforma forms are out of
  scope. OAuth supports the `client_credentials` grant (not the interactive
  authorization-code flow). See `docs/mcp-tools.md` / `docs/http-api.md`.
- **Found a rough edge?** Note the exact command + error — it should become either
  a code fix or a clearer help/error message.
