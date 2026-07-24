#!/usr/bin/env bash
# Group-(a) deploy artifacts smoke test (JN-46). Runs in CI and locally:
#   - helm lint + template (default and toggled values)
#   - docker build of the image
# Fails on the first error.
set -euo pipefail
cd "$(dirname "$0")/../.."

echo "== helm lint =="
helm lint chart

echo "== helm template (default) =="
helm template t chart >/dev/null

echo "== helm template (toggles: ingress/bot/serviceMonitor/hpa/pdb) =="
helm template t chart \
  --set ingress.enabled=true \
  --set command[0]=jira-nano-bot \
  --set serviceMonitor.enabled=true \
  --set autoscaling.enabled=true \
  --set podDisruptionBudget.enabled=true >/dev/null

echo "== docker build =="
DOCKER_BUILDKIT=1 docker build -t jira-nano:ci-test .

echo "OK: deploy artifacts validated"
