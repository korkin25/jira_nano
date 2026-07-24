"""Parse and serialize ``tickets/JN-<n>.md`` (JN-1 / JN-D3).

Round-trip must be stable: ``dumps(loads(text)) == text`` for canonical files.
Frontmatter keys are emitted in a fixed order and conditional keys are omitted
when not applicable (see ``docs/ticket-schema.md``).
"""
from __future__ import annotations

from .models import Ticket

#: Deterministic frontmatter key order (minimizes diffs).
FRONTMATTER_KEY_ORDER: tuple[str, ...] = (
    "id",
    "type",
    "title",
    "status",
    "priority",
    "assignee",
    "reporter",
    "watchers",
    "labels",
    "blocked",
    "blocked_reason",
    "resolution",
    "parent",
    "links",
    "created",
    "updated",
)

#: Comment block header, e.g. ``<!-- c id=1 author=x source=telegram at=... -->``.
COMMENT_HEADER = "<!-- c id={id} author={author} source={source} at={at} -->"


def loads(text: str) -> Ticket:
    """Parse a ticket markdown document into a :class:`Ticket`. TODO(JN-1)."""
    raise NotImplementedError


def dumps(ticket: Ticket) -> str:
    """Serialize a :class:`Ticket` to markdown (fixed key order). TODO(JN-1)."""
    raise NotImplementedError
