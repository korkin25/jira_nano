"""SQLite query cache (derived, rebuildable) — serves all reads.

Git is the source of truth; this cache is never authoritative and can be rebuilt
from the ticket files and the user directory at any time. Split across:

- ``schema``   — tables/indexes/FTS + schema version (JN-4)
- ``rebuild``  — full rebuild from disk (JN-5)
- ``upsert``   — incremental single-row upsert (JN-6)
- ``queries``  — search / list / board (JN-8)
"""
from __future__ import annotations

from pathlib import Path


class Cache:
    """Facade over the SQLite cache connection."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        # TODO(JN-4): connect(sqlite3), ensure schema/version, expose helpers.
