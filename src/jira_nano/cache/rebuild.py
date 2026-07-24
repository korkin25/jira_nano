"""Full cache rebuild from disk (JN-5).

Walks ``tickets/*.md`` and ``.jira_nano/`` (users, workflow), parses them, and
repopulates the cache. Idempotent; triggered on demand, on version mismatch, and
after external Git changes.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path


def rebuild(conn: sqlite3.Connection, root: Path) -> None:
    """Repopulate the whole cache from the ticket files + directory. TODO(JN-5)."""
    raise NotImplementedError
