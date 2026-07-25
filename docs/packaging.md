# Packaging & distribution (`JN-27`)

`jira_nano` is a standard Python package (`jira-nano`) built with **hatchling**
(src layout). The core stays lightweight; each integration surface is an optional
extra.

## Install

**[pipx](https://pipx.pypa.io/) is the recommended installer** — it puts the
`jira-nano` / `jira-nano-mcp` commands on your PATH in an isolated environment.

```bash
# core only (CLI over a local ticket repo)
pipx install jira-nano

# with a surface (extras):
pipx install "jira-nano[mcp]"        # MCP server
pipx install "jira-nano[http]"       # HTTP Jira REST API
pipx install "jira-nano[telegram]"   # Telegram bot mirror
pipx install "jira-nano[mcp,http,telegram]"  # everything
```

`uv tool install "jira-nano[...]"` works identically if you prefer uv.

> **From source** (dev / unreleased changes), install straight from GitHub:
>
> ```bash
> pipx install "jira-nano[mcp,http,telegram] @ git+https://github.com/korkin25/jira_nano.git"
> ```

## Console scripts

| Command | Purpose |
|---------|---------|
| `jira-nano` | CLI over the service layer (`create`/`get`/`list`/`search`/`transition`/`assign`/`comment`/`board`) — `JN-38` |
| `jira-nano-mcp` | run the MCP server over stdio (`JIRA_NANO_REPO` selects the repo) — `JN-26` |
| `jira-nano-mcp-http` | run the MCP server over remote streamable-HTTP — `JN-34` |

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

## Publishing to PyPI (merge to `rc`/`release`, no tags)

`pipx install jira-nano` pulls from **PyPI**, so the package has to be published
there first. Publishing follows the shared release standard: a **merge IS the
release** — there are no git tags. The vendored `.github/workflows/release.yml`
runs `on: push: branches: [rc, release]` and publishes the version computed by
**GitVersion** (`GitVersion.yml`): a merge to `rc` publishes a **pre-release**
(`X.Y.ZrcN`), a merge to `release` publishes the **stable** `X.Y.Z`. **One-time
setup — done by the maintainer:**

1. **Register** at <https://pypi.org> — verify your email and enable 2FA. Check
   that the name `jira-nano` is available (pick another if it is taken).
2. **Configure Trusted Publishing** (recommended — no API token stored in the
   repo). On PyPI → *Your projects* → *Publishing* → add a **pending GitHub
   publisher**:
   - Owner: `korkin25` · Repository: `jira_nano`
   - Workflow: `release.yml` · Environment: `pypi`
3. **Publish**: merge `dev` → `rc` (pre-release) or `dev` → `rc` → `release`
   (stable). `release.yml` derives the version from GitVersion, runs
   `hatch version <semver>`, builds, and uploads via OIDC — no manual dispatch and
   no version is ever hand-written.

Prefer the command line with an API token instead of Trusted Publishing:

```bash
uv build
uv publish        # or: twine upload dist/*   (needs a PyPI token)
```
