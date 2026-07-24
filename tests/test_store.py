"""Git ticket store (pygit2) — JN-2."""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pygit2
import pytest

from jira_nano.models import Ticket
from jira_nano.store import GitTicketStore

_T0 = datetime(2026, 7, 24, 9, 0, 0, tzinfo=UTC)


def _ticket(tid: str = "JN-1", **over: Any) -> Ticket:
    data: dict[str, Any] = {
        "id": tid,
        "title": "t",
        "reporter": "eugeny",
        "created": _T0,
        "updated": _T0,
    }
    data.update(over)
    return Ticket(**data)


@pytest.fixture
def store(tmp_path: Path) -> GitTicketStore:
    pygit2.init_repository(str(tmp_path), bare=False)
    return GitTicketStore(tmp_path)


def test_write_creates_file_and_commit(store: GitTicketStore, tmp_path: Path) -> None:
    sha = store.write(_ticket(), message="feat: JN-1 create")
    assert (tmp_path / "tickets" / "JN-1.md").exists()
    assert isinstance(sha, str) and len(sha) == 40
    assert [h["message"] for h in store.history("JN-1")] == ["feat: JN-1 create"]


def test_read_roundtrip(store: GitTicketStore) -> None:
    t = _ticket(title="Roundtrip", labels=["x"])
    store.write(t, message="feat: JN-1 create")
    assert store.read("JN-1") == t


def test_list_ids(store: GitTicketStore) -> None:
    store.write(_ticket("JN-1"), message="c1")
    store.write(_ticket("JN-2"), message="c2")
    assert store.list_ids() == ["JN-1", "JN-2"]


def test_history_tracks_changes(store: GitTicketStore) -> None:
    store.write(_ticket(title="v1"), message="feat: JN-1 create")
    store.write(_ticket(title="v2"), message="chore: JN-1 edit")
    assert [h["message"] for h in store.history("JN-1")] == [
        "chore: JN-1 edit",
        "feat: JN-1 create",
    ]


def test_second_write_preserves_first(store: GitTicketStore) -> None:
    store.write(_ticket("JN-1"), message="c1")
    store.write(_ticket("JN-2"), message="c2")
    assert store.read("JN-1").id == "JN-1"
    assert sorted(store.list_ids()) == ["JN-1", "JN-2"]
