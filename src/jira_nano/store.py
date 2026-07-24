"""Git-backed ticket store using pygit2 (JN-2).

Git is the source of truth; every write is a commit with a Conventional-Commit
message referencing the ticket id. Reads for callers go through the cache — this
store is the write path and the history/audit reader.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pygit2

from .config import TICKETS_DIRNAME
from .models import Ticket
from .serialization import dumps, loads

_AUTHOR_NAME = "jira_nano"
_AUTHOR_EMAIL = "jira_nano@localhost"


def _blob_oid(tree: Any, rel: str) -> Any:
    try:
        return tree[rel].id
    except KeyError:
        return None


class GitTicketStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.repo = pygit2.Repository(str(self.root))
        self.tickets_dir = self.root / TICKETS_DIRNAME

    def _path(self, ticket_id: str) -> Path:
        return self.tickets_dir / f"{ticket_id}.md"

    def _rel(self, ticket_id: str) -> str:
        return f"{TICKETS_DIRNAME}/{ticket_id}.md"

    def read(self, ticket_id: str) -> Ticket:
        """Read and parse ``tickets/<id>.md`` from the working tree."""
        return loads(self._path(ticket_id).read_text(encoding="utf-8"))

    def list_ids(self) -> list[str]:
        """List all ticket ids present in ``tickets/``."""
        if not self.tickets_dir.exists():
            return []
        return sorted(p.stem for p in self.tickets_dir.glob("JN-*.md"))

    def write(self, ticket: Ticket, *, message: str) -> str:
        """Serialize, stage, and commit the ticket; return the commit sha."""
        self.tickets_dir.mkdir(parents=True, exist_ok=True)
        self._path(ticket.id).write_text(dumps(ticket), encoding="utf-8")
        index = self.repo.index
        index.read()
        index.add(self._rel(ticket.id))
        index.write()
        tree = index.write_tree()
        sig = pygit2.Signature(_AUTHOR_NAME, _AUTHOR_EMAIL)
        parents = [] if self.repo.head_is_unborn else [self.repo.head.target]
        oid = self.repo.create_commit("HEAD", sig, sig, message, tree, parents)
        return str(oid)

    def history(self, ticket_id: str) -> list[dict[str, Any]]:
        """Commit history for a ticket (the audit trail), newest first."""
        if self.repo.head_is_unborn:
            return []
        rel = self._rel(ticket_id)
        out: list[dict[str, Any]] = []
        for commit in self.repo.walk(self.repo.head.target, pygit2.enums.SortMode.TIME):
            cur = _blob_oid(commit.tree, rel)
            if not commit.parents:
                touched = cur is not None
            else:
                touched = any(_blob_oid(p.tree, rel) != cur for p in commit.parents)
            if touched:
                out.append(
                    {
                        "sha": str(commit.id),
                        "message": commit.message.strip(),
                        "author": commit.author.name,
                        "time": commit.commit_time,
                    }
                )
        return out
