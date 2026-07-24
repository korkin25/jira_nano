"""Sequential ``JN-<n>`` id allocation (JN-3).

Ids are mandatory, sequential, and **never reused** — a retired id stays retired.
Allocation is ``max(existing) + 1`` under a lock; archived tickets keep the max
monotonic since their files are never removed.
"""
from __future__ import annotations

from pathlib import Path

ID_PREFIX = "JN-"


def allocate(tickets_dir: Path) -> str:
    """Return the next ``JN-<n>`` id (never reused). TODO(JN-3)."""
    raise NotImplementedError


def parse_number(ticket_id: str) -> int:
    """Return the numeric part of a ``JN-<n>`` id. TODO(JN-3)."""
    raise NotImplementedError
