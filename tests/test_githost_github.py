"""GitHub integration — JN-22."""
from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from typing import Any

import pygit2
import pytest
from fastapi.testclient import TestClient

from jira_nano.githost.github import parse_github
from jira_nano.githost.webhook import build_webhook_app
from jira_nano.models import Status
from jira_nano.service import TicketService


def _pr(action: str, merged: bool = False, title: str = "JN-1: fix") -> dict[str, Any]:
    return {
        "action": action,
        "pull_request": {
            "title": title,
            "number": 7,
            "merged": merged,
            "html_url": "https://github.com/acme/proj/pull/7",
            "user": {"login": "korkin"},
        },
    }


def test_pr_opened() -> None:
    event = parse_github(_pr("opened"))
    assert event is not None
    assert event.kind == "pr_opened"
    assert event.ids == ["JN-1"]
    assert event.ref == "#7"
    assert event.author == "korkin"


def test_pr_merged() -> None:
    assert parse_github(_pr("closed", merged=True)).kind == "pr_merged"  # type: ignore[union-attr]


def test_pr_closed_unmerged() -> None:
    assert parse_github(_pr("closed", merged=False)).kind == "pr_closed"  # type: ignore[union-attr]


def test_unrelated_action_is_none() -> None:
    assert parse_github(_pr("labeled")) is None


def test_push_collects_ids() -> None:
    payload = {
        "ref": "refs/heads/main",
        "sender": {"login": "korkin"},
        "commits": [{"message": "JN-3 fix", "url": "https://github/commit/a"}],
    }
    event = parse_github(payload)
    assert event is not None and event.kind == "push" and event.ids == ["JN-3"]


@pytest.fixture
def service(tmp_path: Path) -> TicketService:
    pygit2.init_repository(str(tmp_path), bare=False)
    return TicketService(tmp_path)


def test_end_to_end_via_webhook(service: TicketService) -> None:
    service.create(title="Fix", reporter="e")
    body = json.dumps(_pr("opened")).encode()
    sig = "sha256=" + hmac.new(b"gh", body, hashlib.sha256).hexdigest()
    app = build_webhook_app(service, {"github": "gh"}, {"github": parse_github})
    client = TestClient(app)
    r = client.post(
        "/webhooks/github",
        content=body,
        headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"},
    )
    assert r.status_code == 200
    ticket = service.get("JN-1")
    assert ticket.status is Status.in_review
    assert any(link.ref == "#7" for link in ticket.links)
