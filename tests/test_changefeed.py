"""Git change-feed — JN-35."""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pygit2

from jira_nano.changefeed import changes_between, diff_tickets
from jira_nano.models import Comment, Link, LinkType, Ticket
from jira_nano.service import TicketService

_T0 = datetime(2026, 7, 24, 9, 0, 0, tzinfo=UTC)


def _ticket(**over: Any) -> Ticket:
    data: dict[str, Any] = {
        "id": "JN-1",
        "title": "t",
        "reporter": "e",
        "created": _T0,
        "updated": _T0,
    }
    data.update(over)
    return Ticket(**data)


def _kinds(events: list[Any]) -> list[str]:
    return [e.kind for e in events]


def test_created() -> None:
    assert _kinds(diff_tickets(None, _ticket())) == ["created"]


def test_status_change() -> None:
    events = diff_tickets(_ticket(status="todo"), _ticket(status="in-progress"))
    assert _kinds(events) == ["status_changed"]
    assert events[0].details == {"from": "todo", "to": "in-progress"}


def test_assignee_and_blocked() -> None:
    events = diff_tickets(
        _ticket(), _ticket(assignee="korkin25", blocked=True, blocked_reason="x")
    )
    assert set(_kinds(events)) == {"assignee_changed", "blocked_changed"}


def test_comment_added() -> None:
    new = _ticket(comments=[Comment(id=1, author="k", source="telegram", at=_T0, body="hi")])
    events = diff_tickets(_ticket(), new)
    assert _kinds(events) == ["comment_added"]
    assert events[0].details["author"] == "k"


def test_link_added_ignores_telegram() -> None:
    tg = _ticket(links=[Link(type=LinkType.telegram, url="tg://forum_topic/1", ref="1")])
    assert diff_tickets(_ticket(), tg) == []
    mr = _ticket(links=[Link(type=LinkType.mr, url="https://x/mr/1")])
    assert _kinds(diff_tickets(_ticket(), mr)) == ["link_added"]


def test_changes_between_commits(tmp_path: Path) -> None:
    pygit2.init_repository(str(tmp_path), bare=False)
    service = TicketService(tmp_path)
    created = service.create(title="a", reporter="e")
    repo = pygit2.Repository(str(tmp_path))
    first = str(repo.head.target)
    service.assign(created.id, "korkin25")
    service.transition(created.id, "in-progress")
    second = str(pygit2.Repository(str(tmp_path)).head.target)

    kinds = {e.kind for e in changes_between(tmp_path, first, second)}
    assert {"assignee_changed", "status_changed"} <= kinds
