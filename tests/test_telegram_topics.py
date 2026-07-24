"""Forum topic management — JN-15."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pygit2
import pytest

from conftest import FakeGateway
from jira_nano.models import LinkType
from jira_nano.service import TicketService
from jira_nano.telegram.topics import ensure_topic, topic_id_of, topic_name


@pytest.fixture
def service(tmp_path: Path) -> TicketService:
    pygit2.init_repository(str(tmp_path), bare=False)
    return TicketService(tmp_path)


def test_topic_name(service: TicketService) -> None:
    t = service.create(title="Fix login", reporter="e")
    assert topic_name(t) == "JN-1: Fix login"


def test_ensure_creates_and_persists(service: TicketService, gateway: FakeGateway) -> None:
    t = service.create(title="Fix", reporter="e")
    topic_id = asyncio.run(ensure_topic(service, gateway, t.id))
    assert topic_id == 101
    assert gateway.calls == ["JN-1: Fix"]
    links = service.get(t.id).links
    assert topic_id_of(links) == 101
    assert any(link.type is LinkType.telegram for link in links)


def test_ensure_reuses_existing(service: TicketService, gateway: FakeGateway) -> None:
    t = service.create(title="x", reporter="e")
    first = asyncio.run(ensure_topic(service, gateway, t.id))
    second = asyncio.run(ensure_topic(service, gateway, t.id))
    assert first == second
    assert len(gateway.calls) == 1
