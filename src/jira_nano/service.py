"""CRUD service layer — the single validated entry point (JN-7).

Every front door (MCP, HTTP, CLI, the Telegram bot) calls this one layer. Writes
**commit to Git first, then upsert the cache**; reads are served from the cache.
The API is shaped MCP-first (JN-D4 / JN-D6). Status transitions are validated in
Phase 2 (JN-10); here ``create`` sets the initial ``todo`` and ``update`` edits
fields only.
"""
from __future__ import annotations

from pathlib import Path

from .models import Ticket


class TicketService:
    def __init__(self, root: Path) -> None:
        self.root = root
        # TODO(JN-7): wire GitTicketStore (JN-2), Cache (JN-4..8), id allocator
        # (JN-3), and the config/user directory (JN-28).

    def create(self, *, title: str, reporter: str, **fields: object) -> Ticket:
        """Allocate an id, write initial ``todo``, commit, then upsert cache. TODO(JN-7)."""
        raise NotImplementedError

    def get(self, ticket_id: str) -> Ticket:
        """Read a ticket from the cache. TODO(JN-7)."""
        raise NotImplementedError

    def update(self, ticket_id: str, **fields: object) -> Ticket:
        """Edit fields, commit, then upsert cache. TODO(JN-7)."""
        raise NotImplementedError
