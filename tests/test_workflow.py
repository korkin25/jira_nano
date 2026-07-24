"""Workflow engine — transitions, guards, blocked flag — JN-10 / JN-D1."""
from __future__ import annotations

from pathlib import Path

import pygit2
import pytest

from jira_nano.config import DEFAULT_WORKFLOW
from jira_nano.errors import TransitionError
from jira_nano.models import Status
from jira_nano.service import TicketService
from jira_nano.workflow import legal_transitions


@pytest.fixture
def service(tmp_path: Path) -> TicketService:
    pygit2.init_repository(str(tmp_path), bare=False)
    return TicketService(tmp_path)


def test_legal_transitions_default() -> None:
    assert legal_transitions(DEFAULT_WORKFLOW, "todo") == ["in-progress", "archived"]
    assert legal_transitions(DEFAULT_WORKFLOW, "done") == ["todo"]


def test_get_transitions(service: TicketService) -> None:
    t = service.create(title="a", reporter="e")
    assert service.get_transitions(t.id) == ["in-progress", "archived"]


def test_illegal_transition_raises(service: TicketService) -> None:
    t = service.create(title="a", reporter="e")
    with pytest.raises(TransitionError):
        service.transition(t.id, "done")  # not reachable from todo


def test_guard_blocks_in_progress_without_assignee(service: TicketService) -> None:
    t = service.create(title="a", reporter="e")
    with pytest.raises(TransitionError):
        service.transition(t.id, "in-progress")


def test_transition_succeeds_when_guard_satisfied(service: TicketService) -> None:
    t = service.create(title="a", reporter="e")
    service.assign(t.id, "korkin25")
    moved = service.transition(t.id, "in-progress")
    assert moved.status is Status.in_progress


def test_transition_to_archived_then_reopen(service: TicketService) -> None:
    t = service.create(title="a", reporter="e")
    service.transition(t.id, "archived")
    assert service.get(t.id).status is Status.archived
    reopened = service.transition(t.id, "todo")  # archived -> todo (revive)
    assert reopened.status is Status.todo


def test_set_and_clear_blocked(service: TicketService) -> None:
    t = service.create(title="a", reporter="e")
    blocked = service.set_blocked(t.id, "waiting on JN-2")
    assert blocked.blocked is True
    assert blocked.blocked_reason == "waiting on JN-2"
    cleared = service.clear_blocked(t.id)
    assert cleared.blocked is False
    assert cleared.blocked_reason is None
