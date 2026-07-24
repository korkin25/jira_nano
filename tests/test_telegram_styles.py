"""Topic status icons / colours — JN-17."""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pygit2
import pytest

from conftest import FakeGateway
from jira_nano.config import DEFAULT_WORKFLOW
from jira_nano.models import Ticket
from jira_nano.service import TicketService
from jira_nano.telegram.topics import (
    header,
    refresh_topic,
    status_icon,
    topic_color,
    topic_title,
)

_T0 = datetime(2026, 7, 24, 9, 0, 0, tzinfo=UTC)


def _ticket(**over: Any) -> Ticket:
    data: dict[str, Any] = {
        "id": "JN-1",
        "title": "Fix",
        "reporter": "e",
        "created": _T0,
        "updated": _T0,
    }
    data.update(over)
    return Ticket(**data)


def test_topic_title_status_icon() -> None:
    assert topic_title(DEFAULT_WORKFLOW, _ticket(status="todo")) == "🟡 JN-1: Fix"
    assert topic_title(DEFAULT_WORKFLOW, _ticket(status="in-progress")) == "🔵 JN-1: Fix"


def test_topic_title_blocked() -> None:
    assert topic_title(DEFAULT_WORKFLOW, _ticket(blocked=True)) == "🟡🚫 JN-1: Fix"


def test_topic_color() -> None:
    assert topic_color(DEFAULT_WORKFLOW, _ticket(status="todo")) == "yellow"
    assert topic_color(DEFAULT_WORKFLOW, _ticket(status="done")) == "green"


def test_status_icon() -> None:
    assert status_icon(DEFAULT_WORKFLOW, _ticket(status="in-review")) == "🟣"


def test_header_format() -> None:
    assert header(DEFAULT_WORKFLOW, _ticket()) == "🟡 <b>Fix</b> <code>JN-1</code>"


@pytest.fixture
def service(tmp_path: Path) -> TicketService:
    pygit2.init_repository(str(tmp_path), bare=False)
    return TicketService(tmp_path)


def test_refresh_topic_renames_on_status(service: TicketService, gateway: FakeGateway) -> None:
    created = service.create(title="Fix", reporter="e")
    service.assign(created.id, "korkin25")
    service.transition(created.id, "in-progress")
    asyncio.run(refresh_topic(service, gateway, created.id))
    assert gateway.edits[-1][1] == "🔵 JN-1: Fix"
