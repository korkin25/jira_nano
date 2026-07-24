"""Ticket model validation — JN-1 / JN-D3."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from pydantic import ValidationError

from jira_nano.models import Status, Ticket

_T0 = datetime(2026, 7, 24, 9, 0, 0, tzinfo=UTC)


def _ticket(**over: Any) -> Ticket:
    data: dict[str, Any] = {
        "id": "JN-1",
        "title": "Example",
        "reporter": "eugeny",
        "created": _T0,
        "updated": _T0,
    }
    data.update(over)
    return Ticket(**data)


def test_minimal_ticket_defaults() -> None:
    t = _ticket()
    assert t.status is Status.todo
    assert t.type.value == "task"
    assert t.priority.value == "medium"
    assert t.assignee is None
    assert t.blocked is False
    assert t.watchers == [] and t.labels == [] and t.links == []


@pytest.mark.parametrize("bad_id", ["J-1", "JN-0", "JN-01", "jn-1", "JN-", "42"])
def test_invalid_id_rejected(bad_id: str) -> None:
    with pytest.raises(ValidationError):
        _ticket(id=bad_id)


def test_invalid_parent_rejected() -> None:
    with pytest.raises(ValidationError):
        _ticket(parent="oops")


def test_blocked_reason_requires_blocked() -> None:
    with pytest.raises(ValidationError):
        _ticket(blocked=False, blocked_reason="waiting")
    # allowed when blocked
    assert _ticket(blocked=True, blocked_reason="waiting").blocked_reason == "waiting"


def test_resolution_only_when_archived() -> None:
    with pytest.raises(ValidationError):
        _ticket(status="todo", resolution="wontfix")
    resolved = _ticket(status="archived", resolution="wontfix")
    assert resolved.resolution is not None and resolved.resolution.value == "wontfix"


def test_updated_not_before_created() -> None:
    with pytest.raises(ValidationError):
        _ticket(created=_T0, updated=_T0 - timedelta(seconds=1))
