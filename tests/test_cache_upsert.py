"""Incremental cache upsert — JN-6."""
from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import Any

from jira_nano.cache.schema import create_schema
from jira_nano.cache.upsert import upsert_ticket, upsert_user
from jira_nano.models import Ticket
from jira_nano.users import User

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


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)
    return conn


def _one(conn: sqlite3.Connection, sql: str) -> Any:
    return conn.execute(sql).fetchone()[0]


def test_update_reflects_and_stays_single_row() -> None:
    conn = _conn()
    upsert_ticket(conn, _ticket("JN-1", title="v1", status="todo"))
    upsert_ticket(conn, _ticket("JN-1", title="v2", status="in-progress"))
    assert _one(conn, "SELECT count(*) FROM tickets") == 1
    assert _one(conn, "SELECT title FROM tickets WHERE id='JN-1'") == "v2"
    assert _one(conn, "SELECT status FROM tickets WHERE id='JN-1'") == "in-progress"


def test_join_rows_are_replaced() -> None:
    conn = _conn()
    upsert_ticket(conn, _ticket("JN-1", labels=["a", "b"]))
    upsert_ticket(conn, _ticket("JN-1", labels=["c"]))
    labels = {r[0] for r in conn.execute("SELECT label FROM ticket_labels WHERE ticket_id='JN-1'")}
    assert labels == {"c"}


def test_fts_is_updated() -> None:
    conn = _conn()
    upsert_ticket(conn, _ticket("JN-1", description="alpha"))
    upsert_ticket(conn, _ticket("JN-1", description="beta"))
    matched = "SELECT count(*) FROM tickets_fts WHERE tickets_fts MATCH ?"
    assert conn.execute(matched, ("alpha",)).fetchone()[0] == 0
    assert conn.execute(matched, ("beta",)).fetchone()[0] == 1


def test_siblings_untouched() -> None:
    conn = _conn()
    upsert_ticket(conn, _ticket("JN-1", title="one"))
    upsert_ticket(conn, _ticket("JN-2", title="two"))
    upsert_ticket(conn, _ticket("JN-1", title="one-edited"))
    assert _one(conn, "SELECT title FROM tickets WHERE id='JN-2'") == "two"
    assert _one(conn, "SELECT count(*) FROM tickets") == 2


def test_upsert_user_replaces() -> None:
    conn = _conn()
    upsert_user(conn, User(handle="a", telegram="@old"))
    upsert_user(conn, User(handle="a", telegram="@new"))
    assert _one(conn, "SELECT count(*) FROM users") == 1
    assert _one(conn, "SELECT telegram FROM users WHERE handle='a'") == "@new"
