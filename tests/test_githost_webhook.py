"""Webhook receiver + normalized event model — JN-36."""
from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from typing import Any

import pygit2
import pytest
from fastapi.testclient import TestClient

from jira_nano.githost.webhook import (
    GitHostEvent,
    build_app_from_env,
    build_webhook_app,
    verify_github,
    verify_gitlab,
)
from jira_nano.models import Status
from jira_nano.service import TicketService


def _parser(host: str) -> Any:
    def parse(payload: dict[str, Any]) -> GitHostEvent:
        return GitHostEvent(
            host=host,
            kind=payload["kind"],
            ids=payload["ids"],
            url=payload.get("url"),
            author=payload.get("author"),
        )

    return parse


@pytest.fixture
def service(tmp_path: Path) -> TicketService:
    pygit2.init_repository(str(tmp_path), bare=False)
    return TicketService(tmp_path)


def test_verify_gitlab() -> None:
    assert verify_gitlab("s", "s")
    assert not verify_gitlab("s", "x")
    assert not verify_gitlab("s", None)


def test_verify_github() -> None:
    body = b'{"a":1}'
    sig = "sha256=" + hmac.new(b"s", body, hashlib.sha256).hexdigest()
    assert verify_github("s", sig, body)
    assert not verify_github("s", "sha256=bad", body)


def test_gitlab_webhook_dispatches(service: TicketService) -> None:
    service.create(title="x", reporter="e")
    app = build_webhook_app(service, {"gitlab": "secret"}, {"gitlab": _parser("gitlab")})
    client = TestClient(app)
    r = client.post(
        "/webhooks/gitlab",
        json={"kind": "mr_opened", "ids": ["JN-1"], "url": "https://x/mr/1", "author": "korkin25"},
        headers={"X-Gitlab-Token": "secret"},
    )
    assert r.status_code == 200
    ticket = service.get("JN-1")
    assert ticket.status is Status.in_review
    assert any(link.url == "https://x/mr/1" for link in ticket.links)


def test_bad_signature_rejected(service: TicketService) -> None:
    app = build_webhook_app(service, {"gitlab": "secret"}, {"gitlab": _parser("gitlab")})
    client = TestClient(app)
    r = client.post(
        "/webhooks/gitlab", json={"kind": "mr_opened", "ids": []}, headers={"X-Gitlab-Token": "no"}
    )
    assert r.status_code == 401


def test_github_signature_verified(service: TicketService) -> None:
    service.create(title="x", reporter="e")
    body = json.dumps({"kind": "pr_opened", "ids": ["JN-1"], "author": "korkin25"}).encode()
    sig = "sha256=" + hmac.new(b"ghsecret", body, hashlib.sha256).hexdigest()
    app = build_webhook_app(service, {"github": "ghsecret"}, {"github": _parser("github")})
    client = TestClient(app)
    r = client.post(
        "/webhooks/github",
        content=body,
        headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"},
    )
    assert r.status_code == 200
    assert service.get("JN-1").status is Status.in_review


def test_build_app_from_env_wires_parsers(
    service: TicketService, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GITLAB_WEBHOOK_SECRET", "gl-secret")
    service.create(title="x", reporter="e")
    client = TestClient(build_app_from_env(service))
    r = client.post(
        "/webhooks/gitlab",
        json={
            "object_kind": "merge_request",
            "object_attributes": {
                "action": "open",
                "title": "JN-1 fix",
                "iid": 5,
                "url": "https://x/mr/5",
            },
            "user": {"username": "korkin25"},
        },
        headers={"X-Gitlab-Token": "gl-secret"},
    )
    assert r.status_code == 200
    assert service.get("JN-1").status is Status.in_review
