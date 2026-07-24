"""Background cache sync — JN-29."""
from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pygit2
import pytest

from jira_nano.config import Paths
from jira_nano.models import Ticket
from jira_nano.serialization import dumps
from jira_nano.store import GitTicketStore
from jira_nano.sync import sync_once

_T0 = datetime(2026, 7, 24, 9, 0, 0, tzinfo=UTC)


def _ticket(tid: str, **over: Any) -> Ticket:
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
def repo(tmp_path: Path) -> Path:
    pygit2.init_repository(str(tmp_path), bare=False)
    return tmp_path


def _title(root: Path, tid: str) -> Any:
    conn = sqlite3.connect(str(Paths.for_repo(root).cache_db))
    return conn.execute("SELECT title FROM tickets WHERE id = ?", (tid,)).fetchone()


def _count(root: Path) -> int:
    conn = sqlite3.connect(str(Paths.for_repo(root).cache_db))
    return int(conn.execute("SELECT count(*) FROM tickets").fetchone()[0])


def test_first_sync_populates(repo: Path) -> None:
    store = GitTicketStore(repo)
    store.write(_ticket("JN-1"), message="c1")
    store.write(_ticket("JN-2"), message="c2")
    assert sync_once(repo) == 2
    assert _count(repo) == 2


def test_sync_after_new_commit(repo: Path) -> None:
    store = GitTicketStore(repo)
    store.write(_ticket("JN-1"), message="c1")
    sync_once(repo)
    store.write(_ticket("JN-2", title="added"), message="c2")
    assert sync_once(repo) == 1
    assert _title(repo, "JN-2") == ("added",)


def test_sync_no_changes(repo: Path) -> None:
    store = GitTicketStore(repo)
    store.write(_ticket("JN-1"), message="c1")
    sync_once(repo)
    assert sync_once(repo) == 0


def test_sync_picks_up_working_tree_edit(repo: Path) -> None:
    store = GitTicketStore(repo)
    store.write(_ticket("JN-1", title="orig"), message="c1")
    sync_once(repo)
    (repo / "tickets" / "JN-1.md").write_text(
        dumps(_ticket("JN-1", title="edited")), encoding="utf-8"
    )
    assert sync_once(repo) == 1
    assert _title(repo, "JN-1") == ("edited",)
