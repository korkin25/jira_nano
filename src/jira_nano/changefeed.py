"""Git change-feed — semantic per-ticket events from committed changes (JN-35).

The Telegram mirror (JN-16/JN-18) reacts to committed ticket changes rather than
to local mutations, so it reflects updates from every source (MCP/HTTP/CLI/git
pull). :func:`diff_tickets` computes events from two ticket states;
:func:`changes_between` derives them from two commits (built on the JN-29 diff
mechanism).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pygit2

from .config import TICKETS_DIRNAME
from .models import LinkType, Ticket
from .serialization import loads


@dataclass(frozen=True)
class Event:
    kind: str
    ticket_id: str
    details: dict[str, Any]


def diff_tickets(old: Ticket | None, new: Ticket) -> list[Event]:
    """Compute the semantic change events between two states of a ticket."""
    if old is None:
        return [Event("created", new.id, {"status": str(new.status)})]

    events: list[Event] = []
    if old.status != new.status:
        events.append(
            Event("status_changed", new.id, {"from": str(old.status), "to": str(new.status)})
        )
    if old.assignee != new.assignee:
        events.append(Event("assignee_changed", new.id, {"from": old.assignee, "to": new.assignee}))
    if old.blocked != new.blocked:
        events.append(
            Event("blocked_changed", new.id, {"blocked": new.blocked, "reason": new.blocked_reason})
        )

    old_comment_ids = {c.id for c in old.comments}
    for comment in new.comments:
        if comment.id not in old_comment_ids:
            events.append(
                Event(
                    "comment_added",
                    new.id,
                    {
                        "comment_id": comment.id,
                        "author": comment.author,
                        "body": comment.body,
                        "source": comment.source,
                    },
                )
            )

    old_links = {(link.type, link.url) for link in old.links}
    for link in new.links:
        if link.type is LinkType.telegram:  # internal mapping, not a user-facing change
            continue
        if (link.type, link.url) not in old_links:
            events.append(Event("link_added", new.id, {"type": str(link.type), "url": link.url}))

    if old.title != new.title or old.description != new.description:
        events.append(Event("updated", new.id, {}))
    return events


def _tid_from_path(path: str) -> str | None:
    prefix = f"{TICKETS_DIRNAME}/"
    if path.startswith(prefix) and path.endswith(".md"):
        stem = path[len(prefix) : -len(".md")]
        if stem.startswith("JN-"):
            return stem
    return None


def _ticket_at(repo: Any, commit: Any, ticket_id: str) -> Ticket | None:
    try:
        entry = commit.tree[f"{TICKETS_DIRNAME}/{ticket_id}.md"]
    except KeyError:
        return None
    blob = repo[entry.id]
    return loads(blob.data.decode("utf-8"))


def changes_between(root: Path, old_sha: str, new_sha: str) -> list[Event]:
    """Derive change events for every ticket touched between two commits."""
    repo: Any = pygit2.Repository(str(Path(root)))
    old_commit = repo.revparse_single(old_sha)
    new_commit = repo.revparse_single(new_sha)
    ticket_ids: set[str] = set()
    for delta in repo.diff(old_commit.tree, new_commit.tree).deltas:
        for path in (delta.old_file.path, delta.new_file.path):
            tid = _tid_from_path(path)
            if tid is not None:
                ticket_ids.add(tid)
    events: list[Event] = []
    for ticket_id in sorted(ticket_ids):
        new_ticket = _ticket_at(repo, new_commit, ticket_id)
        if new_ticket is not None:
            events.extend(diff_tickets(_ticket_at(repo, old_commit, ticket_id), new_ticket))
    return events
