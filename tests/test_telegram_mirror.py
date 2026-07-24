"""Telegram auto-trigger mirror — JN-16/JN-18/JN-35."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pygit2
import pytest

from conftest import FakeGateway
from jira_nano.changefeed import Event
from jira_nano.service import TicketService
from jira_nano.telegram.mirror import (
    dispatch_events,
    mirror_since,
    read_cursor,
    write_cursor,
)
from jira_nano.telegram.topics import topic_title
from jira_nano.users import UserDirectory


@pytest.fixture
def service(tmp_path: Path) -> TicketService:
    pygit2.init_repository(str(tmp_path), bare=False)
    cfg = tmp_path / ".jira_nano"
    cfg.mkdir()
    (cfg / "users.yaml").write_text("korkin25:\n  telegram: '@korkin25'\n")
    return TicketService(tmp_path)


def _directory(service: TicketService) -> UserDirectory:
    return UserDirectory.load(service.paths.config_dir)


def _head(service: TicketService) -> str:
    return str(pygit2.Repository(str(service.paths.root)).head.target)


# --- dispatch_events -------------------------------------------------------


def test_dispatch_assignee_pings_without_update_line(
    service: TicketService, gateway: FakeGateway
) -> None:
    t = service.create(title="Fix", reporter="e")
    service.assign(t.id, "korkin25")
    events = [Event("assignee_changed", t.id, {"from": None, "to": "korkin25"})]
    asyncio.run(dispatch_events(service, gateway, _directory(service), events))
    # Exactly one post — the ping — and no separate "assignee_changed" update line.
    assert len(gateway.posts) == 1
    _, text = gateway.posts[0]
    assert "@korkin25" in text
    assert "assigned to" in text


def test_dispatch_status_changed_renames_and_posts(
    service: TicketService, gateway: FakeGateway
) -> None:
    t = service.create(title="Fix", reporter="e")
    service.assign(t.id, "korkin25")
    service.transition(t.id, "in-progress")
    events = [Event("status_changed", t.id, {"from": "todo", "to": "in-progress"})]
    asyncio.run(dispatch_events(service, gateway, _directory(service), events))
    assert gateway.edits[-1][1] == topic_title(service.workflow, service.get(t.id))
    assert any("in-progress" in text for _, text in gateway.posts)


def test_dispatch_skips_telegram_comment(
    service: TicketService, gateway: FakeGateway
) -> None:
    t = service.create(title="Fix", reporter="e")
    events = [
        Event("comment_added", t.id, {"author": "k", "body": "hi", "source": "telegram"})
    ]
    asyncio.run(dispatch_events(service, gateway, _directory(service), events))
    assert gateway.posts == []


# --- cursor ----------------------------------------------------------------


def test_cursor_round_trips(service: TicketService) -> None:
    assert read_cursor(service.conn) is None
    write_cursor(service.conn, "deadbeef")
    service.conn.commit()
    assert read_cursor(service.conn) == "deadbeef"
    write_cursor(service.conn, "cafef00d")
    service.conn.commit()
    assert read_cursor(service.conn) == "cafef00d"


# --- mirror_since ----------------------------------------------------------


def test_mirror_since_first_call_baselines(
    service: TicketService, gateway: FakeGateway
) -> None:
    service.create(title="Fix", reporter="e")
    head = _head(service)
    result = asyncio.run(mirror_since(service, gateway, _directory(service)))
    assert result == head
    assert read_cursor(service.conn) == head
    assert gateway.posts == []


def test_mirror_since_posts_new_events(
    service: TicketService, gateway: FakeGateway
) -> None:
    service.create(title="First", reporter="e")
    # First run baselines (no replay of history).
    asyncio.run(mirror_since(service, gateway, _directory(service)))
    baseline = read_cursor(service.conn)
    assert baseline is not None

    second = service.create(title="Second", reporter="e")
    new_head = _head(service)
    assert new_head != baseline

    result = asyncio.run(mirror_since(service, gateway, _directory(service)))
    assert result == new_head
    assert read_cursor(service.conn) == new_head
    assert any(second.id in text for _, text in gateway.posts)


def test_mirror_since_rebaselines_on_unresolvable_cursor(
    service: TicketService, gateway: FakeGateway
) -> None:
    service.create(title="Fix", reporter="e")
    head = _head(service)
    write_cursor(service.conn, "0" * 40)  # a sha that resolves to nothing
    service.conn.commit()
    result = asyncio.run(mirror_since(service, gateway, _directory(service)))
    assert result == head
    assert read_cursor(service.conn) == head
    assert gateway.posts == []
