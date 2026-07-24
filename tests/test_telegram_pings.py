"""Assignment pings — JN-16."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pygit2
import pytest

from conftest import FakeGateway
from jira_nano.service import TicketService
from jira_nano.telegram.pings import ping_assignee
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


def test_ping_mentions_assignee(service: TicketService, gateway: FakeGateway) -> None:
    t = service.create(title="Fix", reporter="e")
    service.assign(t.id, "korkin25")
    asyncio.run(ping_assignee(service, gateway, _directory(service), t.id))
    assert gateway.posts
    _, text = gateway.posts[-1]
    assert "@korkin25" in text
    assert "JN-1" in text


def test_ping_format(service: TicketService, gateway: FakeGateway) -> None:
    t = service.create(title="Fix", reporter="e")
    service.assign(t.id, "korkin25")
    asyncio.run(ping_assignee(service, gateway, _directory(service), t.id))
    assert gateway.posts[-1][1] == "🟡 <b>Fix</b> <code>JN-1</code>\n↳ 👤 assigned to @korkin25"


def test_ping_unknown_handle_falls_back(service: TicketService, gateway: FakeGateway) -> None:
    t = service.create(title="Fix", reporter="e")
    service.assign(t.id, "stranger")
    asyncio.run(ping_assignee(service, gateway, _directory(service), t.id))
    assert "@stranger" in gateway.posts[-1][1]


def test_ping_no_assignee(service: TicketService, gateway: FakeGateway) -> None:
    t = service.create(title="x", reporter="e")
    asyncio.run(ping_assignee(service, gateway, _directory(service), t.id))
    assert gateway.posts == []
