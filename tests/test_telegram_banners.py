"""Static status banners — photo cards for the Telegram mirror."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from jira_nano.models import Ticket
from jira_nano.telegram.banners import banner_bytes, banner_for

_T0 = datetime(2026, 7, 24, 9, 0, 0, tzinfo=UTC)


def _ticket(**over: Any) -> Ticket:
    data: dict[str, Any] = {
        "id": "JN-1", "title": "Fix", "reporter": "e", "created": _T0, "updated": _T0,
    }
    data.update(over)
    return Ticket(**data)


def test_banner_bytes_returns_png() -> None:
    data = banner_bytes("in-review")
    assert data is not None
    assert data.startswith(b"\x89PNG")


def test_banner_bytes_unknown_is_none() -> None:
    assert banner_bytes("nope") is None


def test_banner_for_uses_status_banner() -> None:
    ticket = _ticket(status="in-review")
    assert banner_for(ticket) == banner_bytes("in-review")


def test_banner_for_blocked_takes_precedence() -> None:
    ticket = _ticket(status="in-progress", blocked=True, blocked_reason="waiting")
    assert banner_for(ticket) == banner_bytes("blocked")
