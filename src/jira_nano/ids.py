"""Sequential ``JN-<n>`` id allocation (JN-3).

Ids are mandatory, sequential, and **never reused** — a retired id stays retired.
Allocation is ``max(existing) + 1``; archived tickets keep the max monotonic
since their files are never removed. Callers (the service, JN-7) serialize
allocate-then-write so concurrent creates cannot collide.
"""
from __future__ import annotations

import re
from pathlib import Path

ID_PREFIX = "JN-"
_NUM_RE = re.compile(r"^JN-([1-9]\d*)$")


def parse_number(ticket_id: str) -> int:
    """Return the numeric part of a ``JN-<n>`` id, or raise ``ValueError``."""
    match = _NUM_RE.match(ticket_id)
    if match is None:
        raise ValueError(f"invalid ticket id: {ticket_id!r}")
    return int(match.group(1))


def allocate(tickets_dir: Path) -> str:
    """Return the next ``JN-<n>`` id (``max(existing) + 1``; never reused)."""
    tickets_dir = Path(tickets_dir)
    max_n = 0
    if tickets_dir.exists():
        for path in tickets_dir.glob("JN-*.md"):
            match = _NUM_RE.match(path.stem)
            if match is not None:
                max_n = max(max_n, int(match.group(1)))
    return f"{ID_PREFIX}{max_n + 1}"
