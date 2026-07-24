# jira-nano Helm chart

Deploys [jira_nano](https://github.com/korkin25/jira_nano) — a git-backed,
Jira-compatible issue tracker — from the image published to GHCR
(`ghcr.io/korkin25/jira-nano`). The chart is packaged and pushed as an OCI
artifact to `ghcr.io/korkin25/charts/jira-nano` by CI.

Adapted from the BNPL "application" chart, stripped of platform coupling
(ArgoCD globals, ESO/Vault, GatewayAPI, Liquibase) for a portable GitHub/GHCR
deployment.

## Install

```bash
helm install jira-nano oci://ghcr.io/korkin25/charts/jira-nano --version 0.1.0
```

## Workload

A single-replica **StatefulSet** runs `jira-nano-http` (the HTTP Jira REST API)
on port 8080, fronted by a ClusterIP Service. The git ticket store (the source
of record) and the SQLite cache live on the `data` PVC; an initContainer runs
`jira-nano --repo /data/repo init` (idempotent) before the app starts.

Run a different surface by overriding `command`:

| Surface | `command` |
|---------|-----------|
| HTTP Jira REST (default) | `["jira-nano-http"]` |
| MCP over streamable-HTTP | `["jira-nano-mcp-http"]` |
| Telegram mirror bot | `["jira-nano-bot"]` |
| Git-host webhook receiver | `["jira-nano-webhooks"]` |

## Secrets

The chart never templates secret values. Provide runtime secrets (Telegram bot
token, HTTP auth credentials) via an existing Secret and enable `envFrom.secret`:

```yaml
envFrom:
  secret:
    enabled: true
    name: jira-nano-secrets
```

## Voice / STT model

STT (voice-message transcription) uses a local Whisper model. The model is
**deliberately not baked into the image** (it is large and variable). Instead:

- `voiceModel.enabled: true` (default) creates a PVC (`<release>-models`,
  {{ default "2Gi" }}) mounted at `/models`;
- the ConfigMap points `HF_HOME` and `XDG_CACHE_HOME` at that mount, so the
  model is fetched **on first use** into the PVC and reused across restarts;
- alternatively **devops preloads** it — run `jira-nano-voice-setup` against the
  PVC once, or set `voiceModel.existingClaim` to a pre-populated PVC.

To actually run STT the container also needs the `[voice]` extra (faster-whisper).
The default image ships without it to stay lean; build/use a voice-enabled image
tag when you need in-cluster transcription. This is identical to the tg_notes chart.

## Values of note

| Key | Default | Purpose |
|-----|---------|---------|
| `image.repository` / `image.tag` | `ghcr.io/korkin25/jira-nano` / appVersion | image |
| `command` | `["jira-nano-http"]` | which surface to serve |
| `persistence.size` | `1Gi` | git store + cache PVC |
| `voiceModel.enabled` / `.size` | `true` / `2Gi` | Whisper model cache PVC |
| `envFrom.secret.enabled` | `false` | inject an existing Secret |
| `serviceMonitor.enabled` | `false` | Prometheus Operator scrape |
| `ingress.enabled` | `false` | external access |

Probes are TCP on the serving port (there is no HTTP health endpoint yet).
