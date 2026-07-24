"""Update posts — JN-18."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pygit2
import pytest

from conftest import FakeGateway
from jira_nano.changefeed import Event
from jira_nano.service import TicketService
from jira_nano.telegram.updates import format_event, post_events


def test_format_event() -> None:
    jn = "<code>JN-1</code>"  # ticket id is monospace so it is easy to copy
    assert format_event(Event("status_changed", "JN-1", {"from": "todo", "to": "done"})) == (
        f"{jn}: status todo → done"
    )
    assert format_event(Event("blocked_changed", "JN-1", {"blocked": True})) == f"{jn}: 🚫 blocked"
    assert format_event(Event("comment_added", "JN-1", {"author": "k", "body": "hi"})) == (
        f"{jn}: 💬 k: hi"
    )
    assert format_event(Event("link_added", "JN-1", {"type": "mr", "url": "u"})) == f"{jn}: 🔗 mr u"


def test_format_event_escapes_html() -> None:
    assert format_event(Event("comment_added", "JN-1", {"author": "k", "body": "a < b & c"})) == (
        "<code>JN-1</code>: 💬 k: a &lt; b &amp; c"
    )


@pytest.fixture
def service(tmp_path: Path) -> TicketService:
    pygit2.init_repository(str(tmp_path), bare=False)
    return TicketService(tmp_path)


def test_post_events(service: TicketService, gateway: FakeGateway) -> None:
    t = service.create(title="Fix", reporter="e")
    events = [Event("status_changed", t.id, {"from": "todo", "to": "in-progress"})]
    asyncio.run(post_events(service, gateway, events))
    assert gateway.posts[-1][1] == "<code>JN-1</code>: status todo → in-progress"


def test_post_events_skips_telegram_comments(service: TicketService, gateway: FakeGateway) -> None:
    t = service.create(title="Fix", reporter="e")
    events = [
        Event("comment_added", t.id, {"author": "k", "body": "hi", "source": "telegram"}),
        Event("comment_added", t.id, {"author": "bot", "body": "yo", "source": "mcp"}),
    ]
    asyncio.run(post_events(service, gateway, events))
    assert [p[1] for p in gateway.posts] == ["<code>JN-1</code>: 💬 bot: yo"]
