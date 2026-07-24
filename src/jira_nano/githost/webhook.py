"""Webhook receiver + normalized event model (JN-36 / JN-D4).

A small HTTP listener — **separate** from the public Jira REST API — that verifies
the host signature, hands the raw payload to a host-specific parser (JN-21/JN-22)
producing a normalized :class:`GitHostEvent`, then dispatches it: link the ticket
(JN-23) and advance its status (JN-24). Polling (JN-37) reuses ``dispatch``.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request

from jira_nano.service import TicketService

from .apply import apply_event
from .links import link_ticket


@dataclass
class GitHostEvent:
    host: str  # gitlab | github
    kind: str  # mr_opened | mr_merged | mr_closed | pr_opened | ... | push
    ids: list[str] = field(default_factory=list)
    ref: str | None = None
    url: str | None = None
    author: str | None = None


Parser = Callable[[dict[str, Any]], "GitHostEvent | None"]


def verify_gitlab(secret: str, token: str | None) -> bool:
    return hmac.compare_digest(secret, token or "")


def verify_github(secret: str, signature: str | None, body: bytes) -> bool:
    expected = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature or "")


def _link_type(kind: str) -> str:
    if kind.startswith("mr"):
        return "mr"
    if kind.startswith("pr"):
        return "pr"
    return "commit"


def dispatch(service: TicketService, event: GitHostEvent) -> None:
    """Link the referenced tickets and advance their status for one event."""
    for ticket_id in event.ids:
        if event.url:
            link_ticket(
                service, ticket_id, type=_link_type(event.kind), host=event.host,
                url=event.url, ref=event.ref,
            )
        apply_event(service, ticket_id, event.kind, author=event.author)


def build_webhook_app(
    service: TicketService, secrets: dict[str, str], parsers: dict[str, Parser]
) -> FastAPI:
    """A FastAPI app exposing ``POST /webhooks/{host}`` (gitlab / github)."""
    app = FastAPI(title="jira_nano-webhooks")

    @app.post("/webhooks/{host}")
    async def receive(host: str, request: Request) -> dict[str, bool]:
        body = await request.body()
        secret = secrets.get(host, "")
        if host == "gitlab":
            ok = verify_gitlab(secret, request.headers.get("x-gitlab-token"))
        elif host == "github":
            ok = verify_github(secret, request.headers.get("x-hub-signature-256"), body)
        else:
            raise HTTPException(status_code=404, detail="unknown host")
        if not ok:
            raise HTTPException(status_code=401, detail="invalid signature")
        parser = parsers.get(host)
        if parser is None:
            raise HTTPException(status_code=404, detail="no parser for host")
        event = parser(json.loads(body))
        if event is not None:
            dispatch(service, event)
        return {"ok": True}

    return app


def build_app_from_env(service: TicketService) -> FastAPI:
    """Webhook app wired with the GitLab/GitHub parsers and env-based secrets."""
    from .github import parse_github
    from .gitlab import parse_gitlab

    secrets = {
        "gitlab": os.environ.get("GITLAB_WEBHOOK_SECRET", ""),
        "github": os.environ.get("GITHUB_WEBHOOK_SECRET", ""),
    }
    parsers: dict[str, Parser] = {"gitlab": parse_gitlab, "github": parse_github}
    return build_webhook_app(service, secrets, parsers)


def run(repo: Path | None = None) -> None:  # pragma: no cover - server event loop
    """Console entry point: serve the git-host webhook receiver with uvicorn."""
    import uvicorn

    root = Path(repo) if repo is not None else Path(os.environ.get("JIRA_NANO_REPO", "."))
    host = os.environ.get("JIRA_NANO_WEBHOOK_HOST", "0.0.0.0")  # all interfaces; set to restrict
    port = int(os.environ.get("JIRA_NANO_WEBHOOK_PORT", "8081"))
    uvicorn.run(build_app_from_env(TicketService(root)), host=host, port=port)
