"""Full cache rebuild from disk — JN-5."""
from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jira_nano.cache.rebuild import rebuild
from jira_nano.cache.schema import create_schema
from jira_nano.models import Ticket
from jira_nano.serialization import dumps

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


def _repo(tmp_path: Path, *tickets: Ticket, users: str = "") -> Path:
    (tmp_path / "tickets").mkdir(parents=True, exist_ok=True)
    for t in tickets:
        (tmp_path / "tickets" / f"{t.id}.md").write_text(dumps(t), encoding="utf-8")
    cfg = tmp_path / ".jira_nano"
    cfg.mkdir(exist_ok=True)
    if users:
        (cfg / "users.yaml").write_text(users, encoding="utf-8")
    return tmp_path


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)
    return conn


def _one(conn: sqlite3.Connection, sql: str) -> Any:
    return conn.execute(sql).fetchone()[0]


def test_rebuild_populates(tmp_path: Path) -> None:
    root = _repo(
        tmp_path,
        _ticket("JN-1", labels=["backend"], watchers=["alice"], description="find me here"),
        _ticket("JN-2", status="in-progress"),
        users="alice:\n  telegram: '@alice'\n",
    )
    conn = _conn()
    rebuild(conn, root)
    assert _one(conn, "SELECT count(*) FROM tickets") == 2
    assert _one(conn, "SELECT status FROM tickets WHERE id='JN-2'") == "in-progress"
    assert _one(conn, "SELECT count(*) FROM ticket_labels WHERE ticket_id='JN-1'") == 1
    assert _one(conn, "SELECT count(*) FROM ticket_watchers WHERE ticket_id='JN-1'") == 1
    assert _one(conn, "SELECT telegram FROM users WHERE handle='alice'") == "@alice"
    hits = conn.execute(
        "SELECT ticket_id FROM tickets_fts WHERE tickets_fts MATCH 'here'"
    ).fetchall()
    assert hits == [("JN-1",)]


def test_rebuild_is_idempotent(tmp_path: Path) -> None:
    root = _repo(tmp_path, _ticket("JN-1"), _ticket("JN-2"))
    conn = _conn()
    rebuild(conn, root)
    rebuild(conn, root)
    assert _one(conn, "SELECT count(*) FROM tickets") == 2


def test_ticket_json_reconstructs_ticket(tmp_path: Path) -> None:
    original = _ticket("JN-1", labels=["x"], description="body")
    root = _repo(tmp_path, original)
    conn = _conn()
    rebuild(conn, root)
    (raw,) = conn.execute("SELECT ticket_json FROM tickets WHERE id='JN-1'").fetchone()
    assert Ticket.model_validate_json(raw) == original
