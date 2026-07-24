"""Comment pull-back — JN-19."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pygit2
import pytest

from conftest import FakeGateway
from jira_nano.service import TicketService
from jira_nano.telegram.pullback import find_ticket_by_topic, pull_back
from jira_nano.telegram.topics import ensure_topic
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


def test_by_telegram_reverse_lookup(service: TicketService) -> None:
    directory = _directory(service)
    assert directory.by_telegram("@korkin25").handle == "korkin25"  # type: ignore[union-attr]
    assert directory.by_telegram("korkin25").handle == "korkin25"  # type: ignore[union-attr]
    assert directory.by_telegram("nobody") is None


def test_pull_back_writes_comment(service: TicketService, gateway: FakeGateway) -> None:
    t = service.create(title="Fix", reporter="e")
    topic_id = asyncio.run(ensure_topic(service, gateway, t.id))
    result = pull_back(service, _directory(service), topic_id, "@korkin25", "looks good")
    assert result == t.id
    comments = service.get(t.id).comments
    assert comments[-1].author == "korkin25"
    assert comments[-1].source == "telegram"
    assert comments[-1].body == "looks good"


def test_pull_back_unknown_topic(service: TicketService) -> None:
    assert pull_back(service, _directory(service), 999, "@korkin25", "hi") is None


def test_pull_back_unknown_user_falls_back(service: TicketService, gateway: FakeGateway) -> None:
    t = service.create(title="Fix", reporter="e")
    topic_id = asyncio.run(ensure_topic(service, gateway, t.id))
    pull_back(service, _directory(service), topic_id, "@stranger", "hi")
    assert service.get(t.id).comments[-1].author == "stranger"


def test_find_ticket_by_topic(service: TicketService, gateway: FakeGateway) -> None:
    t = service.create(title="x", reporter="e")
    topic_id = asyncio.run(ensure_topic(service, gateway, t.id))
    assert find_ticket_by_topic(service, topic_id) == t.id
    assert find_ticket_by_topic(service, 42) is None
