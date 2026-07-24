"""Polling fallback — JN-37."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pygit2
import pytest

from jira_nano.githost.gitlab import parse_gitlab
from jira_nano.githost.polling import EventKey, poll_once
from jira_nano.models import Status
from jira_nano.service import TicketService


def _mr(title: str = "JN-1: fix") -> dict[str, Any]:
    return {
        "object_kind": "merge_request",
        "object_attributes": {
            "action": "open",
            "title": title,
            "iid": 42,
            "url": "https://gitlab.com/acme/proj/-/merge_requests/42",
        },
        "user": {"username": "korkin25"},
    }


@pytest.fixture
def service(tmp_path: Path) -> TicketService:
    pygit2.init_repository(str(tmp_path), bare=False)
    return TicketService(tmp_path)


def test_poll_dispatches_then_dedupes(service: TicketService) -> None:
    service.create(title="Fix", reporter="e")
    payloads = [_mr()]
    seen: set[EventKey] = set()

    first = poll_once(service, lambda: payloads, parse_gitlab, seen)
    assert first == 1
    ticket = service.get("JN-1")
    assert ticket.status is Status.in_review
    assert any(link.ref == "!42" for link in ticket.links)

    # a second poll of the same data processes nothing
    assert poll_once(service, lambda: payloads, parse_gitlab, seen) == 0
