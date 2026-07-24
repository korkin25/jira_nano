"""Round-trip (de)serialization for tickets/JN-<n>.md — JN-1 / JN-D3."""
from __future__ import annotations

from datetime import UTC, datetime

from jira_nano.models import Comment, Host, Link, LinkType, Priority, Status, Ticket, Type
from jira_nano.serialization import dumps, loads

_T0 = datetime(2026, 7, 24, 9, 0, 0, tzinfo=UTC)
_T1 = datetime(2026, 7, 24, 12, 30, 0, tzinfo=UTC)

CANONICAL = """\
---
id: JN-123
type: task
title: Short summary
status: in-progress
priority: high
assignee: korkin25
reporter: eugeny
watchers:
- eugeny
labels:
- backend
blocked: false
parent: JN-100
links:
- type: mr
  host: gitlab
  url: https://gitlab.com/acme/proj/-/merge_requests/42
  ref: '!42'
created: '2026-07-24T09:00:00Z'
updated: '2026-07-24T12:30:00Z'
---

## Description

Body text.

## Comments

<!-- c id=1 author=korkin25 source=telegram at=2026-07-24T12:30:00Z -->
Pulled-back comment.
"""


def _rich() -> Ticket:
    return Ticket(
        id="JN-123",
        type=Type.task,
        title="Short summary",
        status=Status.in_progress,
        priority=Priority.high,
        assignee="korkin25",
        reporter="eugeny",
        watchers=["eugeny"],
        labels=["backend"],
        blocked=False,
        parent="JN-100",
        links=[Link(type=LinkType.mr, host=Host.gitlab,
                    url="https://gitlab.com/acme/proj/-/merge_requests/42", ref="!42")],
        created=_T0,
        updated=_T1,
        description="Body text.",
        comments=[Comment(id=1, author="korkin25", source="telegram", at=_T1,
                          body="Pulled-back comment.")],
    )


def test_semantic_roundtrip() -> None:
    t = _rich()
    assert loads(dumps(t)) == t


def test_dumps_matches_canonical() -> None:
    assert dumps(_rich()) == CANONICAL


def test_loads_parses_canonical() -> None:
    t = loads(CANONICAL)
    assert t.id == "JN-123"
    assert t.status is Status.in_progress
    assert t.parent == "JN-100"
    assert t.links[0].type is LinkType.mr and t.links[0].ref == "!42"
    assert t.description == "Body text."
    assert len(t.comments) == 1
    assert t.comments[0].author == "korkin25"
    assert t.comments[0].body == "Pulled-back comment."


def test_dumps_is_idempotent() -> None:
    assert dumps(loads(CANONICAL)) == CANONICAL
