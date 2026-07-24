"""Git-host event → transition — JN-24."""
from __future__ import annotations

from pathlib import Path

import pygit2
import pytest

from jira_nano.config import DEFAULT_WORKFLOW
from jira_nano.githost.apply import apply_event, shortest_path
from jira_nano.models import Status
from jira_nano.service import TicketService


@pytest.fixture
def service(tmp_path: Path) -> TicketService:
    pygit2.init_repository(str(tmp_path), bare=False)
    return TicketService(tmp_path)


def _in_review(service: TicketService) -> str:
    t = service.create(title="x", reporter="e")
    service.assign(t.id, "korkin25")
    service.transition(t.id, "in-progress")
    service.transition(t.id, "in-review")
    return t.id


def test_shortest_path() -> None:
    assert shortest_path(DEFAULT_WORKFLOW, "todo", "in-review") == [
        "todo",
        "in-progress",
        "in-review",
    ]
    assert shortest_path(DEFAULT_WORKFLOW, "in-review", "done") == ["in-review", "done"]


def test_mr_opened_auto_advances_and_assigns(service: TicketService) -> None:
    t = service.create(title="x", reporter="e")
    result = apply_event(service, t.id, "mr_opened", author="korkin25")
    assert result is not None
    assert result.status is Status.in_review
    assert result.assignee == "korkin25"  # auto-assigned to satisfy the guard


def test_mr_merged_to_done(service: TicketService) -> None:
    tid = _in_review(service)
    result = apply_event(service, tid, "mr_merged")
    assert result is not None and result.status is Status.done


def test_mr_closed_goes_back_to_in_progress(service: TicketService) -> None:
    tid = _in_review(service)
    result = apply_event(service, tid, "mr_closed")
    assert result is not None and result.status is Status.in_progress


def test_unmapped_event_is_noop(service: TicketService) -> None:
    t = service.create(title="x", reporter="e")
    assert apply_event(service, t.id, "star_added") is None
    assert service.get(t.id).status is Status.todo
