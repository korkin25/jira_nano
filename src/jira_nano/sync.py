"""Background cache sync — keep the cache consistent with Git (JN-29).

Compares the cache's stored HEAD sha against the repo ``HEAD``, diffs the changed
files via pygit2, and upserts them; also picks up uncommitted working-tree edits.
This is what refreshes the cache after an external ``git pull`` or out-of-band
edit. It also feeds the git change-feed consumed by the Telegram mirror (JN-35).
"""
from __future__ import annotations

from pathlib import Path


def sync_once(root: Path) -> int:
    """Refresh the cache for changed tickets/users; return the count changed. TODO(JN-29)."""
    raise NotImplementedError


def watch(root: Path) -> None:
    """Run the background sync loop (fs events + periodic HEAD check). TODO(JN-29)."""
    raise NotImplementedError
