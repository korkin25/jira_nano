"""Cache-backed reads: search / list / board (JN-8).

These back the ``search`` / ``list`` / ``board`` service operations and, later,
the MCP search tool and the HTTP JQL subset (JN-30).
"""
from __future__ import annotations

import sqlite3

from jira_nano.models import Status, Ticket


def search(conn: sqlite3.Connection, text: str | None = None, **filters: object) -> list[Ticket]:
    """FTS + field-filtered search. TODO(JN-8)."""
    raise NotImplementedError


def list_tickets(conn: sqlite3.Connection, **filters: object) -> list[Ticket]:
    """Filtered list (status/assignee/label/priority/type). TODO(JN-8)."""
    raise NotImplementedError


def board(conn: sqlite3.Connection) -> dict[Status, list[Ticket]]:
    """Tickets grouped by workflow status. TODO(JN-8)."""
    raise NotImplementedError
