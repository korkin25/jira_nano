"""Git-backed ticket store using pygit2 (JN-2).

Git is the source of truth; every write is a commit with a Conventional-Commit
message referencing the ticket id. Reads for callers go through the cache — this
store is the write path and the history/audit reader.
"""
from __future__ import annotations

from pathlib import Path

from .models import Ticket


class GitTicketStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        # TODO(JN-2): open pygit2.Repository(root); resolve tickets/ dir.

    def read(self, ticket_id: str) -> Ticket:
        """Read and parse ``tickets/<id>.md`` from the working tree. TODO(JN-2)."""
        raise NotImplementedError

    def write(self, ticket: Ticket, *, message: str) -> str:
        """Serialize, stage, and commit the ticket; return the commit sha. TODO(JN-2)."""
        raise NotImplementedError

    def list_ids(self) -> list[str]:
        """List all ticket ids present in ``tickets/``. TODO(JN-2)."""
        raise NotImplementedError

    def history(self, ticket_id: str) -> list[dict]:
        """Commit history for a ticket (the audit trail). TODO(JN-2)."""
        raise NotImplementedError
