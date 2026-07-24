"""JQL subset parser + executor — JN-30."""
from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import Any

import pytest

from jira_nano.cache.schema import create_schema
from jira_nano.cache.upsert import upsert_ticket
from jira_nano.errors import JqlError
from jira_nano.jira.jql import run
from jira_nano.models import Ticket

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


def _conn(*tickets: Ticket) -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)
    for t in tickets:
        upsert_ticket(conn, t)
    return conn


def _ids(rows: list[Ticket]) -> list[str]:
    return [t.id for t in rows]


def test_eq() -> None:
    conn = _conn(_ticket("JN-1", status="todo"), _ticket("JN-2", status="in-progress"))
    assert _ids(run(conn, "status = todo")) == ["JN-1"]


def test_and() -> None:
    conn = _conn(
        _ticket("JN-1", status="todo", assignee="korkin25"),
        _ticket("JN-2", status="todo", assignee="bob"),
    )
    assert _ids(run(conn, "status = todo AND assignee = korkin25")) == ["JN-1"]


def test_or() -> None:
    conn = _conn(
        _ticket("JN-1", status="done"),
        _ticket("JN-2", status="archived"),
        _ticket("JN-3", status="todo"),
    )
    assert _ids(run(conn, "status = done OR status = archived")) == ["JN-1", "JN-2"]


def test_in() -> None:
    conn = _conn(
        _ticket("JN-1", status="todo"),
        _ticket("JN-2", status="done"),
        _ticket("JN-3", status="archived"),
    )
    assert _ids(run(conn, "status IN (todo, done)")) == ["JN-1", "JN-2"]


def test_not_eq() -> None:
    conn = _conn(_ticket("JN-1", status="todo"), _ticket("JN-2", status="done"))
    assert _ids(run(conn, "status != todo")) == ["JN-2"]


def test_text_match() -> None:
    conn = _conn(_ticket("JN-1", description="alpha beta"), _ticket("JN-2", description="gamma"))
    assert _ids(run(conn, 'text ~ "beta"')) == ["JN-1"]


def test_labels() -> None:
    conn = _conn(_ticket("JN-1", labels=["backend"]), _ticket("JN-2", labels=["frontend"]))
    assert _ids(run(conn, "labels = backend")) == ["JN-1"]


def test_order_by_desc() -> None:
    conn = _conn(_ticket("JN-1", status="todo"), _ticket("JN-2", status="todo"))
    assert _ids(run(conn, "status = todo ORDER BY key DESC")) == ["JN-2", "JN-1"]


def test_unknown_field_raises() -> None:
    conn = _conn(_ticket("JN-1"))
    with pytest.raises(JqlError):
        run(conn, "bogus = x")
