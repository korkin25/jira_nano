"""CRUD service layer — JN-7."""
from __future__ import annotations

from pathlib import Path

import pygit2
import pytest

from jira_nano.errors import TicketNotFoundError
from jira_nano.models import Status
from jira_nano.service import TicketService
from jira_nano.store import GitTicketStore


@pytest.fixture
def service(tmp_path: Path) -> TicketService:
    pygit2.init_repository(str(tmp_path), bare=False)
    return TicketService(tmp_path)


def test_create_sets_defaults_and_persists(service: TicketService, tmp_path: Path) -> None:
    t = service.create(title="Hello", reporter="eugeny")
    assert t.id == "JN-1"
    assert t.status is Status.todo
    assert t.reporter == "eugeny"
    assert (tmp_path / "tickets" / "JN-1.md").exists()
    assert service.get("JN-1").title == "Hello"


def test_create_allocates_sequential(service: TicketService) -> None:
    a = service.create(title="a", reporter="e")
    b = service.create(title="b", reporter="e")
    assert (a.id, b.id) == ("JN-1", "JN-2")


def test_create_accepts_extra_fields(service: TicketService) -> None:
    t = service.create(title="a", reporter="e", labels=["backend"], priority="high")
    assert t.labels == ["backend"]
    assert t.priority.value == "high"


def test_get_unknown_raises(service: TicketService) -> None:
    with pytest.raises(TicketNotFoundError):
        service.get("JN-99")


def test_update_edits_and_bumps_updated(service: TicketService) -> None:
    created = service.create(title="v1", reporter="e")
    updated = service.update(created.id, title="v2", labels=["x"])
    assert updated.title == "v2"
    assert updated.labels == ["x"]
    assert updated.updated >= updated.created
    assert service.get(created.id).title == "v2"


def test_update_commits_a_second_time(service: TicketService, tmp_path: Path) -> None:
    created = service.create(title="v1", reporter="e")
    service.update(created.id, status="in-progress")
    history = GitTicketStore(tmp_path).history(created.id)
    assert len(history) == 2


def test_service_list_search_board(service: TicketService) -> None:
    service.create(title="alpha bug", reporter="e", labels=["backend"])
    b = service.create(title="beta task", reporter="e")
    service.update(b.id, status="in-progress")

    assert {t.id for t in service.list_tickets()} == {"JN-1", "JN-2"}
    assert [t.id for t in service.list_tickets(label="backend")] == ["JN-1"]
    assert [t.id for t in service.search("beta")] == ["JN-2"]
    board = service.board()
    assert {s.value: [t.id for t in ts] for s, ts in board.items()} == {
        "todo": ["JN-1"],
        "in-progress": ["JN-2"],
    }
