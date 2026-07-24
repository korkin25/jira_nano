"""Cache-backed search / list / board — JN-8."""
from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import Any

from jira_nano.cache.queries import board, list_tickets, search
from jira_nano.cache.schema import create_schema
from jira_nano.cache.upsert import upsert_ticket
from jira_nano.models import Status, Ticket

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


def test_list_all() -> None:
    conn = _conn(_ticket("JN-1"), _ticket("JN-2"))
    assert [t.id for t in list_tickets(conn)] == ["JN-1", "JN-2"]


def test_list_filter_status() -> None:
    conn = _conn(_ticket("JN-1", status="todo"), _ticket("JN-2", status="in-progress"))
    assert [t.id for t in list_tickets(conn, status="in-progress")] == ["JN-2"]


def test_list_filter_label() -> None:
    conn = _conn(_ticket("JN-1", labels=["x"]), _ticket("JN-2", labels=["y"]))
    assert [t.id for t in list_tickets(conn, label="x")] == ["JN-1"]


def test_search_text() -> None:
    conn = _conn(_ticket("JN-1", description="alpha beta"), _ticket("JN-2", description="gamma"))
    assert [t.id for t in search(conn, "beta")] == ["JN-1"]


def test_search_text_and_filter() -> None:
    conn = _conn(
        _ticket("JN-1", description="shared", status="todo"),
        _ticket("JN-2", description="shared", status="done"),
    )
    assert [t.id for t in search(conn, "shared", status="done")] == ["JN-2"]


def test_search_no_match_is_empty() -> None:
    conn = _conn(_ticket("JN-1", description="alpha"))
    assert search(conn, "nomatch") == []


def test_board_groups_by_status() -> None:
    conn = _conn(
        _ticket("JN-1", status="todo"),
        _ticket("JN-2", status="todo"),
        _ticket("JN-3", status="done"),
    )
    grouped = {s: [t.id for t in ts] for s, ts in board(conn).items()}
    assert grouped == {Status.todo: ["JN-1", "JN-2"], Status.done: ["JN-3"]}
