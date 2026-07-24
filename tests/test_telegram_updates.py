"""Update posts — JN-18."""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pygit2
import pytest

from conftest import FakeGateway
from jira_nano.changefeed import Event
from jira_nano.config import DEFAULT_WORKFLOW
from jira_nano.models import Ticket
from jira_nano.service import TicketService
from jira_nano.telegram.updates import post_events, render_event

_T0 = datetime(2026, 7, 24, 9, 0, 0, tzinfo=UTC)


def _ticket(**over: Any) -> Ticket:
    data: dict[str, Any] = {
        "id": "JN-1", "title": "Fix", "reporter": "e", "created": _T0, "updated": _T0,
    }
    data.update(over)
    return Ticket(**data)


def _render(ticket: Ticket, event: Event) -> str:
    return render_event(DEFAULT_WORKFLOW, ticket, event)


def test_render_status_changed() -> None:
    out = _render(
        _ticket(status="in-review"),
        Event("status_changed", "JN-1", {"from": "in-progress", "to": "in-review"}),
    )
    assert out == "🟣 <b>Fix</b> <code>JN-1</code>\n↳ in-progress → <b>in-review</b>"


def test_render_created() -> None:
    assert _render(_ticket(status="todo"), Event("created", "JN-1", {"status": "todo"})) == (
        "🟡 <b>Fix</b> <code>JN-1</code>\n↳ 🆕 created"
    )


def test_render_blocked() -> None:
    assert _render(_ticket(blocked=True), Event("blocked_changed", "JN-1", {"blocked": True})) == (
        "🟡 <b>Fix</b> <code>JN-1</code>\n↳ 🚫 blocked"
    )


def test_render_comment_uses_blockquote() -> None:
    assert _render(_ticket(), Event("comment_added", "JN-1", {"author": "k", "body": "hi"})) == (
        "🟡 <b>Fix</b> <code>JN-1</code>\n💬 <b>k</b>:\n<blockquote expandable>hi</blockquote>"
    )


def test_render_link_is_hyperlink() -> None:
    out = _render(
        _ticket(), Event("link_added", "JN-1", {"type": "mr", "url": "https://x/1", "ref": "!7"})
    )
    assert out == '🟡 <b>Fix</b> <code>JN-1</code>\n↳ 🔗 <a href="https://x/1">mr !7</a>'


def test_render_escapes_html() -> None:
    out = _render(
        _ticket(title="A <b> & c"), Event("comment_added", "JN-1", {"author": "k", "body": "x < y"})
    )
    assert "A &lt;b&gt; &amp; c" in out
    assert "x &lt; y" in out


@pytest.fixture
def service(tmp_path: Path) -> TicketService:
    pygit2.init_repository(str(tmp_path), bare=False)
    return TicketService(tmp_path)


def test_post_events(service: TicketService, gateway: FakeGateway) -> None:
    t = service.create(title="Fix", reporter="e")
    events = [Event("status_changed", t.id, {"from": "todo", "to": "in-progress"})]
    asyncio.run(post_events(service, gateway, events))
    assert gateway.posts[-1][1] == "🟡 <b>Fix</b> <code>JN-1</code>\n↳ todo → <b>in-progress</b>"


def test_post_events_skips_telegram_comments(service: TicketService, gateway: FakeGateway) -> None:
    t = service.create(title="Fix", reporter="e")
    events = [
        Event("comment_added", t.id, {"author": "k", "body": "hi", "source": "telegram"}),
        Event("comment_added", t.id, {"author": "bot", "body": "yo", "source": "mcp"}),
    ]
    asyncio.run(post_events(service, gateway, events))
    assert [p[1] for p in gateway.posts] == [
        "🟡 <b>Fix</b> <code>JN-1</code>\n💬 <b>bot</b>:\n<blockquote expandable>yo</blockquote>"
    ]
