"""CRUD service layer — the single validated entry point (JN-7).

Every front door (MCP, HTTP, CLI, the Telegram bot) calls this one layer. Writes
**commit to Git first, then upsert the cache**; reads are served from the cache.
The API is shaped MCP-first (JN-D4 / JN-D6). Status transitions are validated in
Phase 2 (JN-10); here ``create`` sets the initial status and ``update`` edits
fields only.
"""
from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .cache import queries
from .cache.rebuild import rebuild
from .cache.schema import create_schema
from .cache.upsert import upsert_ticket
from .config import Paths, load_workflow
from .errors import TicketNotFoundError
from .ids import allocate
from .models import Comment, Host, Link, LinkType, Status, Ticket
from .store import GitTicketStore
from .workflow import check_transition, legal_transitions


def _now() -> datetime:
    return datetime.now(UTC)


class TicketService:
    def __init__(self, root: Path) -> None:
        self.paths = Paths.for_repo(Path(root))
        self.paths.config_dir.mkdir(parents=True, exist_ok=True)
        self.store = GitTicketStore(self.paths.root)
        self.workflow = load_workflow(self.paths.config_dir)
        self.conn = sqlite3.connect(str(self.paths.cache_db))
        create_schema(self.conn)
        rebuild(self.conn, self.paths.root)

    def create(self, *, title: str, reporter: str, **fields: Any) -> Ticket:
        """Allocate an id, write the initial ticket, commit, then upsert cache."""
        tid = allocate(self.paths.tickets)
        now = _now()
        ticket = Ticket(
            id=tid,
            title=title,
            reporter=reporter,
            status=Status(self.workflow.initial),
            created=now,
            updated=now,
            **fields,
        )
        self.store.write(ticket, message=f"feat({tid}): create")
        upsert_ticket(self.conn, ticket)
        self.conn.commit()
        return ticket

    def get(self, ticket_id: str) -> Ticket:
        """Read a ticket from the cache."""
        row = self.conn.execute(
            "SELECT ticket_json FROM tickets WHERE id = ?", (ticket_id,)
        ).fetchone()
        if row is None:
            raise TicketNotFoundError(ticket_id)
        return Ticket.model_validate_json(row[0])

    def _mutate(self, ticket_id: str, message: str, **changes: Any) -> Ticket:
        """Load, apply ``changes``, bump ``updated``, commit, then upsert cache."""
        data = self.get(ticket_id).model_dump()
        data.update(changes)
        data["updated"] = _now()
        ticket = Ticket(**data)
        self.store.write(ticket, message=message)
        upsert_ticket(self.conn, ticket)
        self.conn.commit()
        return ticket

    def update(self, ticket_id: str, **fields: Any) -> Ticket:
        """Edit fields, commit, then upsert cache. (Transitions: Phase 2 / JN-10.)"""
        return self._mutate(ticket_id, f"chore({ticket_id}): update", **fields)

    def get_transitions(self, ticket_id: str) -> list[str]:
        """Return the legal target statuses from the ticket's current status."""
        return legal_transitions(self.workflow, str(self.get(ticket_id).status))

    def transition(self, ticket_id: str, target: str) -> Ticket:
        """Move the ticket to ``target`` if legal (`JN-D1`); else raise."""
        ticket = self.get(ticket_id)
        check_transition(self.workflow, ticket, target)
        message = f"chore({ticket_id}): {ticket.status} -> {target}"
        return self._mutate(ticket_id, message, status=target)

    def set_blocked(self, ticket_id: str, reason: str | None = None) -> Ticket:
        """Flag the ticket as blocked (impediment), optionally with a reason."""
        return self._mutate(
            ticket_id, f"chore({ticket_id}): blocked", blocked=True, blocked_reason=reason
        )

    def clear_blocked(self, ticket_id: str) -> Ticket:
        """Clear the blocked flag."""
        return self._mutate(
            ticket_id, f"chore({ticket_id}): unblocked", blocked=False, blocked_reason=None
        )

    def assign(self, ticket_id: str, assignee: str | None) -> Ticket:
        """Set the assignee (triggers a Telegram ping in Phase 3)."""
        return self._mutate(ticket_id, f"chore({ticket_id}): assign {assignee}", assignee=assignee)

    def comment(self, ticket_id: str, *, author: str, body: str, source: str = "mcp") -> Ticket:
        """Append a comment to the ticket's log (ids are sequential, never reused)."""
        current = self.get(ticket_id)
        next_id = max((c.id for c in current.comments), default=0) + 1
        new = Comment(id=next_id, author=author, source=source, at=_now(), body=body)
        return self._mutate(
            ticket_id, f"chore({ticket_id}): comment", comments=[*current.comments, new]
        )

    def edit_comment(self, ticket_id: str, comment_id: int, body: str) -> Ticket:
        """Edit an existing comment in place, stamping ``edited``."""
        comments = [
            c.model_copy(update={"body": body, "edited": _now()}) if c.id == comment_id else c
            for c in self.get(ticket_id).comments
        ]
        return self._mutate(
            ticket_id, f"chore({ticket_id}): edit comment {comment_id}", comments=comments
        )

    def get_watchers(self, ticket_id: str) -> list[str]:
        """Return the ticket's watcher handles."""
        return self.get(ticket_id).watchers

    def add_watcher(self, ticket_id: str, handle: str) -> Ticket:
        """Add a watcher (no-op if already present)."""
        current = self.get(ticket_id)
        if handle in current.watchers:
            return current
        return self._mutate(
            ticket_id, f"chore({ticket_id}): add watcher {handle}",
            watchers=[*current.watchers, handle],
        )

    def remove_watcher(self, ticket_id: str, handle: str) -> Ticket:
        """Remove a watcher (no-op if absent)."""
        current = self.get(ticket_id)
        return self._mutate(
            ticket_id, f"chore({ticket_id}): remove watcher {handle}",
            watchers=[w for w in current.watchers if w != handle],
        )

    def link_epic(self, ticket_id: str, parent_id: str) -> Ticket:
        """Link the ticket to a parent epic."""
        message = f"chore({ticket_id}): link to epic {parent_id}"
        return self._mutate(ticket_id, message, parent=parent_id)

    def add_link(
        self,
        ticket_id: str,
        *,
        type: str,
        url: str,
        host: str | None = None,
        ref: str | None = None,
    ) -> Ticket:
        """Append a git-host / remote link to the ticket."""
        current = self.get(ticket_id)
        link = Link(
            type=LinkType(type),
            host=Host(host) if host is not None else None,
            url=url,
            ref=ref,
        )
        return self._mutate(
            ticket_id, f"chore({ticket_id}): add link", links=[*current.links, link]
        )

    def search(self, text: str | None = None, **filters: Any) -> list[Ticket]:
        """Cache-backed full-text + field search."""
        return queries.search(self.conn, text, **filters)

    def list_tickets(self, **filters: Any) -> list[Ticket]:
        """Cache-backed filtered list."""
        return queries.list_tickets(self.conn, **filters)

    def board(self) -> dict[Status, list[Ticket]]:
        """Tickets grouped by workflow status."""
        return queries.board(self.conn)
