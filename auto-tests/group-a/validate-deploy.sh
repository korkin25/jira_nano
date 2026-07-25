#!/usr/bin/env bash
# Group-(a) functional smoke test. Chart linting lives in the shared `helm` CI job, so this
# script only proves the IMAGE actually boots and serves an authenticated request:
#   - docker build of the image
#   - boot the HTTP Jira REST API (init a git store, then jira-nano-http)
#   - GET /rest/api/2/myself with a bearer token -> expect 200
# The token is self-contained (a default is baked in), so no CI secret is required.
# Contract (open-ci-actions functional runner): exit 0 = pass, 77 = skip, other = fail.
set -euo pipefail
cd "$(dirname "$0")/../.."

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not available — skipping functional smoke test"
  exit 77
fi

PORT="${JIRA_NANO_HTTP_PORT:-8080}"
# "<name>:<token>" — the probe authenticates with the token half. A default keeps the test
# self-contained; override JIRA_NANO_TOKENS to exercise a real token set.
TOKENS="${JIRA_NANO_TOKENS:-ci:ci-functional-token}"
TOKEN="${TOKENS##*:}"

# Where the published port is reachable. On a laptop / GitHub Actions the daemon is local,
# so 127.0.0.1. On GitLab CI the container runs on the docker:dind *service* and its ports
# live in that service's netns — reachable at host `docker`, never localhost. Derive the
# host from DOCKER_HOST (e.g. tcp://docker:2376 -> docker) when the runner set it.
PROBE_HOST="127.0.0.1"
if [ -n "${DOCKER_HOST:-}" ]; then
  h="$(printf '%s' "${DOCKER_HOST}" | sed -E 's#^[a-z]+://##; s#:.*$##')"
  [ -n "${h}" ] && PROBE_HOST="${h}"
fi

echo "== docker build =="
DOCKER_BUILDKIT=1 docker build -t jira-nano:ci-test .

echo "== boot HTTP API and probe ${PROBE_HOST}:${PORT} =="
docker rm -f jn-ci >/dev/null 2>&1 || true
docker run -d --name jn-ci -p "${PORT}:8080" -e JIRA_NANO_TOKENS="${TOKENS}" \
  --entrypoint sh jira-nano:ci-test \
  -c 'jira-nano --repo /data/repo init && exec jira-nano-http' >/dev/null

code="000"
for _ in $(seq 1 20); do
  code="$(curl -s -o /dev/null -w '%{http_code}' \
    -H "Authorization: Bearer ${TOKEN}" \
    "http://${PROBE_HOST}:${PORT}/rest/api/2/myself" || true)"
  [ "${code}" = "200" ] && break
  sleep 1
done
echo "authenticated GET /rest/api/2/myself -> ${code}"
docker logs jn-ci 2>&1 | tail -15 || true
docker rm -f jn-ci >/dev/null 2>&1 || true
test "${code}" = "200"

echo "OK: image boots and serves an authenticated request on :${PORT}"
