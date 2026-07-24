"""Cache-backed reads: search / list / board (JN-8).

These back the ``search`` / ``list`` / ``board`` service operations and, later,
the MCP search tool and the HTTP JQL subset (JN-30). Every result is
reconstructed from the ``ticket_json`` column so reads never touch the files.
"""
from __future__ import annotations

import sqlite3
from typing import Any

from jira_nano.models import Status, Ticket


def _tickets(rows: list[Any]) -> list[Ticket]:
    return [Ticket.model_validate_json(r[0]) for r in rows]


def _query(
    conn: sqlite3.Connection,
    *,
    ids: list[str] | None = None,
    status: str | None = None,
    assignee: str | None = None,
    priority: str | None = None,
    type: str | None = None,
    label: str | None = None,
) -> list[Ticket]:
    sql = "SELECT t.ticket_json FROM tickets t"
    params: list[Any] = []
    if label is not None:
        sql += " JOIN ticket_labels l ON l.ticket_id = t.id AND l.label = ?"
        params.append(label)
    clauses: list[str] = []
    if ids is not None:
        if not ids:
            return []
        clauses.append(f"t.id IN ({','.join('?' * len(ids))})")
        params.extend(ids)
    for column, value in (
        ("status", status),
        ("assignee", assignee),
        ("priority", priority),
        ("type", type),
    ):
        if value is not None:
            clauses.append(f"t.{column} = ?")
            params.append(str(value))
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY t.created, t.id"
    return _tickets(conn.execute(sql, params).fetchall())


def list_tickets(
    conn: sqlite3.Connection,
    *,
    status: str | None = None,
    assignee: str | None = None,
    priority: str | None = None,
    type: str | None = None,
    label: str | None = None,
) -> list[Ticket]:
    """Filtered list (status/assignee/priority/type/label)."""
    return _query(
        conn, status=status, assignee=assignee, priority=priority, type=type, label=label
    )


def search(
    conn: sqlite3.Connection,
    text: str | None = None,
    *,
    status: str | None = None,
    assignee: str | None = None,
    priority: str | None = None,
    type: str | None = None,
    label: str | None = None,
) -> list[Ticket]:
    """Full-text (FTS) search over title/description/comments, plus field filters."""
    ids: list[str] | None = None
    if text:
        rows = conn.execute(
            "SELECT ticket_id FROM tickets_fts WHERE tickets_fts MATCH ?", (text,)
        ).fetchall()
        ids = [r[0] for r in rows]
    return _query(
        conn, ids=ids, status=status, assignee=assignee, priority=priority, type=type, label=label
    )


def board(conn: sqlite3.Connection) -> dict[Status, list[Ticket]]:
    """Tickets grouped by workflow status."""
    grouped: dict[Status, list[Ticket]] = {}
    for ticket in _query(conn):
        grouped.setdefault(ticket.status, []).append(ticket)
    return grouped
