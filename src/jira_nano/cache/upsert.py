"""Incremental cache upsert after a local write (JN-6)."""
from __future__ import annotations

import sqlite3

from ..models import Ticket
from ..users import User


def upsert_ticket(conn: sqlite3.Connection, ticket: Ticket) -> None:
    """Upsert one ticket's row + join tables, no full walk. TODO(JN-6)."""
    raise NotImplementedError


def upsert_user(conn: sqlite3.Connection, user: User) -> None:
    """Upsert one user directory row. TODO(JN-6)."""
    raise NotImplementedError
