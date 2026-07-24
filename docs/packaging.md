# Packaging & distribution (`JN-27`)

`jira_nano` is a standard Python package (`jira-nano`) built with **hatchling**
(src layout). The core stays lightweight; each integration surface is an optional
extra.

## Install

```bash
# core only (CLI over a local ticket repo)
uv tool install jira-nano
# or: pipx install jira-nano

# with a surface (extras):
uv tool install "jira-nano[mcp]"     # MCP server
uv tool install "jira-nano[http]"    # HTTP Jira REST API
uv tool install "jira-nano[telegram]"# Telegram bot mirror
uv tool install "jira-nano[mcp,http,telegram]"  # everything
```

## Console scripts

| Command | Purpose |
|---------|---------|
| `jira-nano` | CLI over the service layer (`create`/`get`/`list`/`search`/`transition`/`assign`/`comment`/`board`) — `JN-38` |
| `jira-nano-mcp` | run the MCP server over stdio (`JIRA_NANO_REPO` selects the repo) — `JN-26` |

The HTTP API and Telegram bot are run from their app factories
(`jira_nano.http.app:build_app`, `jira_nano.telegram.bot:build_dispatcher`).

## Agent Skill

The repository itself is the Agent Skill: `SKILL.md` (agentskills.io format) plus
the packaged MCP tools. A sample MCP client config is in `examples/mcp.json`.

## Building

```bash
uv build          # produces dist/*.whl and dist/*.tar.gz
```

CI builds the distribution on every `v*` tag (`.github/workflows/ci.yml`).

## Single-file build (evaluated — `JN-D2`)

Python has no static binary by default. For a self-contained artifact, a
single-file build via **PyInstaller** or **shiv** can be produced from the wheel
in a later step; for now `uv tool install` / `pipx` give reproducible installs.

## Publishing (separate, explicit step)

Publishing to PyPI is intentionally a later, manual step (never automatic):

```bash
uv build
uv publish        # requires PyPI credentials; run only for a tagged release
```
