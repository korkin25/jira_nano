"""Extended service operations: assign / comment / watchers / links — JN-9."""
from __future__ import annotations

from pathlib import Path

import pygit2
import pytest

from jira_nano.models import LinkType
from jira_nano.service import TicketService


@pytest.fixture
def service(tmp_path: Path) -> TicketService:
    pygit2.init_repository(str(tmp_path), bare=False)
    return TicketService(tmp_path)


def test_assign(service: TicketService) -> None:
    t = service.create(title="a", reporter="e")
    assigned = service.assign(t.id, "korkin25")
    assert assigned.assignee == "korkin25"
    assert service.get(t.id).assignee == "korkin25"


def test_comment_appends_sequential_ids(service: TicketService) -> None:
    t = service.create(title="a", reporter="e")
    service.comment(t.id, author="korkin25", body="first", source="telegram")
    result = service.comment(t.id, author="claude", body="second")
    assert [(c.id, c.author, c.body) for c in result.comments] == [
        (1, "korkin25", "first"),
        (2, "claude", "second"),
    ]
    assert result.comments[0].source == "telegram"


def test_edit_comment(service: TicketService) -> None:
    t = service.create(title="a", reporter="e")
    service.comment(t.id, author="korkin25", body="orig")
    edited = service.edit_comment(t.id, 1, "revised")
    assert edited.comments[0].body == "revised"
    assert edited.comments[0].edited is not None


def test_watchers_add_remove(service: TicketService) -> None:
    t = service.create(title="a", reporter="e")
    service.add_watcher(t.id, "alice")
    service.add_watcher(t.id, "bob")
    service.add_watcher(t.id, "alice")  # duplicate no-op
    assert service.get_watchers(t.id) == ["alice", "bob"]
    service.remove_watcher(t.id, "alice")
    assert service.get_watchers(t.id) == ["bob"]


def test_link_epic(service: TicketService) -> None:
    epic = service.create(title="epic", reporter="e", type="epic")
    child = service.create(title="child", reporter="e")
    linked = service.link_epic(child.id, epic.id)
    assert linked.parent == epic.id


def test_add_link(service: TicketService) -> None:
    t = service.create(title="a", reporter="e")
    result = service.add_link(
        t.id, type="mr", url="https://gitlab.com/x/-/merge_requests/42", host="gitlab", ref="!42"
    )
    assert len(result.links) == 1
    assert result.links[0].type is LinkType.mr
    assert result.links[0].ref == "!42"
