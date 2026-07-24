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

from .cache.rebuild import rebuild
from .cache.schema import create_schema
from .cache.upsert import upsert_ticket
from .config import Paths, load_workflow
from .errors import TicketNotFoundError
from .ids import allocate
from .models import Status, Ticket
from .store import GitTicketStore


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

    def update(self, ticket_id: str, **fields: Any) -> Ticket:
        """Edit fields, commit, then upsert cache. (Transitions: Phase 2 / JN-10.)"""
        data = self.get(ticket_id).model_dump()
        data.update(fields)
        data["updated"] = _now()
        ticket = Ticket(**data)
        self.store.write(ticket, message=f"chore({ticket_id}): update")
        upsert_ticket(self.conn, ticket)
        self.conn.commit()
        return ticket
