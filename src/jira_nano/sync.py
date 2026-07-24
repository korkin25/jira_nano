"""Background cache sync — keep the cache consistent with Git (JN-29).

Compares the cache's stored HEAD sha against the repo ``HEAD``, diffs the changed
files via pygit2, and upserts them; also picks up uncommitted working-tree edits.
This is what refreshes the cache after an external ``git pull`` or out-of-band
edit. It also feeds the git change-feed consumed by the Telegram mirror (JN-35).
"""
from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any

import pygit2

from jira_nano.config import Paths
from jira_nano.serialization import loads
from jira_nano.users import UserDirectory

from .cache.rebuild import rebuild
from .cache.schema import create_schema
from .cache.upsert import upsert_ticket, upsert_user

_HEAD_KEY = "head_sha"
_TICKET_PREFIX = "tickets/"


def _tid_from_path(path: str) -> str | None:
    if path.startswith(_TICKET_PREFIX) and path.endswith(".md"):
        stem = path[len(_TICKET_PREFIX) : -len(".md")]
        if stem.startswith("JN-"):
            return stem
    return None


def _read_head(conn: sqlite3.Connection) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (_HEAD_KEY,)).fetchone()
    return row[0] if row else None


def _store_head(conn: sqlite3.Connection, sha: str | None) -> None:
    conn.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (_HEAD_KEY, sha or ""),
    )


def _delete_ticket(conn: sqlite3.Connection, tid: str) -> None:
    conn.execute("DELETE FROM tickets WHERE id = ?", (tid,))
    conn.execute("DELETE FROM ticket_labels WHERE ticket_id = ?", (tid,))
    conn.execute("DELETE FROM ticket_watchers WHERE ticket_id = ?", (tid,))
    conn.execute("DELETE FROM ticket_links WHERE ticket_id = ?", (tid,))
    conn.execute("DELETE FROM tickets_fts WHERE ticket_id = ?", (tid,))


def _changed_ids(repo: Any, stored: str, current: str) -> set[str]:
    changed: set[str] = set()
    old = repo.revparse_single(stored)
    new = repo.revparse_single(current)
    for delta in repo.diff(old.tree, new.tree).deltas:
        for path in (delta.old_file.path, delta.new_file.path):
            tid = _tid_from_path(path)
            if tid is not None:
                changed.add(tid)
    return changed


def sync_once(root: Path) -> int:
    """Refresh the cache for changed tickets/users; return the count changed."""
    paths = Paths.for_repo(Path(root))
    paths.config_dir.mkdir(parents=True, exist_ok=True)
    repo = pygit2.Repository(str(paths.root))
    conn = sqlite3.connect(str(paths.cache_db))
    try:
        create_schema(conn)
        current = None if repo.head_is_unborn else str(repo.head.target)
        stored = _read_head(conn)

        if not stored:
            rebuild(conn, paths.root)
            _store_head(conn, current)
            conn.commit()
            return int(conn.execute("SELECT count(*) FROM tickets").fetchone()[0])

        changed: set[str] = set()
        if current is not None and current != stored:
            changed |= _changed_ids(repo, stored, current)
        for path in repo.status():
            tid = _tid_from_path(path)
            if tid is not None:
                changed.add(tid)

        for tid in changed:
            file = paths.tickets / f"{tid}.md"
            if file.exists():
                upsert_ticket(conn, loads(file.read_text(encoding="utf-8")))
            else:
                _delete_ticket(conn, tid)
        for user in UserDirectory.load(paths.config_dir).all_users():
            upsert_user(conn, user)
        _store_head(conn, current)
        conn.commit()
        return len(changed)
    finally:
        conn.close()


def watch(root: Path, interval: float = 2.0) -> None:  # pragma: no cover - daemon loop
    """Run the background sync loop (periodic HEAD/working-tree check)."""
    while True:
        sync_once(root)
        time.sleep(interval)
