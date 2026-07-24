"""Full cache rebuild from disk (JN-5).

Walks ``tickets/*.md`` and ``.jira_nano/`` (users, workflow), parses them, and
repopulates the cache. Idempotent; triggered on demand, on version mismatch, and
after external Git changes.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from jira_nano.config import Paths
from jira_nano.serialization import loads
from jira_nano.users import UserDirectory

from .upsert import upsert_ticket, upsert_user

_CLEAR = (
    "DELETE FROM tickets",
    "DELETE FROM ticket_labels",
    "DELETE FROM ticket_watchers",
    "DELETE FROM ticket_links",
    "DELETE FROM users",
    "DELETE FROM tickets_fts",
)


def rebuild(conn: sqlite3.Connection, root: Path) -> None:
    """Repopulate the whole cache from the ticket files + directory."""
    paths = Paths.for_repo(Path(root))
    for stmt in _CLEAR:
        conn.execute(stmt)
    if paths.tickets.exists():
        for path in sorted(paths.tickets.glob("JN-*.md")):
            upsert_ticket(conn, loads(path.read_text(encoding="utf-8")))
    for user in UserDirectory.load(paths.config_dir).all_users():
        upsert_user(conn, user)
    conn.commit()
