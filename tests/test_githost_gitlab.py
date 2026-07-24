"""GitLab integration — JN-21."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pygit2
import pytest
from fastapi.testclient import TestClient

from jira_nano.githost.gitlab import parse_gitlab
from jira_nano.githost.webhook import build_webhook_app
from jira_nano.models import Status
from jira_nano.service import TicketService


def _mr(action: str, title: str = "JN-1: fix") -> dict[str, Any]:
    return {
        "object_kind": "merge_request",
        "object_attributes": {
            "action": action,
            "title": title,
            "iid": 42,
            "url": "https://gitlab.com/acme/proj/-/merge_requests/42",
        },
        "user": {"username": "korkin25"},
    }


def test_merge_request_open() -> None:
    event = parse_gitlab(_mr("open"))
    assert event is not None
    assert event.kind == "mr_opened"
    assert event.ids == ["JN-1"]
    assert event.ref == "!42"
    assert event.author == "korkin25"


def test_merge_request_merge() -> None:
    assert parse_gitlab(_mr("merge")).kind == "mr_merged"  # type: ignore[union-attr]


def test_unrelated_action_is_none() -> None:
    assert parse_gitlab(_mr("update")) is None


def test_push_collects_ids() -> None:
    payload = {
        "object_kind": "push",
        "user_username": "korkin25",
        "commits": [
            {"message": "JN-1 wip", "url": "https://gitlab/commit/a"},
            {"message": "JN-2 more", "url": "https://gitlab/commit/b"},
        ],
    }
    event = parse_gitlab(payload)
    assert event is not None
    assert event.kind == "push"
    assert event.ids == ["JN-1", "JN-2"]


@pytest.fixture
def service(tmp_path: Path) -> TicketService:
    pygit2.init_repository(str(tmp_path), bare=False)
    return TicketService(tmp_path)


def test_end_to_end_via_webhook(service: TicketService) -> None:
    service.create(title="Fix", reporter="e")
    app = build_webhook_app(service, {"gitlab": "s"}, {"gitlab": parse_gitlab})
    client = TestClient(app)
    r = client.post("/webhooks/gitlab", json=_mr("open"), headers={"X-Gitlab-Token": "s"})
    assert r.status_code == 200
    ticket = service.get("JN-1")
    assert ticket.status is Status.in_review
    assert any(link.ref == "!42" for link in ticket.links)
