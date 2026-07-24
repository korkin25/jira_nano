# syntax=docker/dockerfile:1
#
# Multi-stage image for jira_nano. Built and pushed to GHCR by CI
# (ghcr.io/korkin25/jira-nano). The default command serves the HTTP Jira REST
# API on :8080; override the entrypoint to run the MCP server, Telegram bot, or
# webhook receiver (see the chart / docker-compose).
#
# The heavy `[voice]` STT stack (faster-whisper + model weights) is deliberately
# NOT baked in — see chart/README.md for the voice-model PVC pattern.

ARG PYTHON_VERSION=3.12

# ---- build: produce a wheel and a self-contained venv -----------------------
FROM python:${PYTHON_VERSION}-slim AS build
ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /src
RUN python -m pip install --upgrade pip build
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN python -m build --wheel --outdir /dist \
 && python -m venv /opt/venv \
 && /opt/venv/bin/pip install "$(echo /dist/*.whl)[http,mcp,telegram]"

# ---- final: slim runtime, non-root ------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS final
LABEL org.opencontainers.image.source="https://github.com/korkin25/jira_nano" \
      org.opencontainers.image.description="jira_nano — git-backed, Jira-compatible issue tracker" \
      org.opencontainers.image.licenses="GPL-3.0-or-later"

# uid/gid 10000 matches the chart's securityContext (runAsNonRoot). Pre-create the
# data + model dirs owned by the app user so bare `docker run` and docker named
# volumes (which inherit the mountpoint's ownership) are writable; in k8s the PVCs
# mount over them (fsGroup 10000).
RUN groupadd -g 10000 app \
 && useradd -u 10000 -g 10000 -m -d /home/app -s /usr/sbin/nologin app \
 && mkdir -p /data /models \
 && chown 10000:10000 /data /models

COPY --from=build /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/home/app \
    JIRA_NANO_REPO=/data/repo \
    JIRA_NANO_HTTP_HOST=0.0.0.0 \
    JIRA_NANO_HTTP_PORT=8080

WORKDIR /app
USER 10000
EXPOSE 8080

# Default: the HTTP Jira REST API. Override CMD for jira-nano-mcp-http /
# jira-nano-bot / jira-nano-webhooks.
ENTRYPOINT ["jira-nano-http"]
