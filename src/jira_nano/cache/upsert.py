"""Cache row writers: single-ticket / single-user upsert (JN-6).

These are the shared writers used by both the full rebuild (JN-5) and the
incremental update after a local write (JN-6). Each upsert fully replaces the
ticket's row and its join/FTS rows, so it is safe to call repeatedly.
"""
from __future__ import annotations

import sqlite3

from jira_nano.models import Ticket
from jira_nano.serialization import iso_utc
from jira_nano.users import User


def upsert_ticket(conn: sqlite3.Connection, ticket: Ticket) -> None:
    """Insert or replace one ticket's row + join/FTS rows."""
    tid = ticket.id
    conn.execute("DELETE FROM tickets WHERE id = ?", (tid,))
    conn.execute("DELETE FROM ticket_labels WHERE ticket_id = ?", (tid,))
    conn.execute("DELETE FROM ticket_watchers WHERE ticket_id = ?", (tid,))
    conn.execute("DELETE FROM ticket_links WHERE ticket_id = ?", (tid,))
    conn.execute("DELETE FROM tickets_fts WHERE ticket_id = ?", (tid,))
    conn.execute(
        "INSERT INTO tickets(id, type, title, status, priority, assignee, reporter, "
        "blocked, blocked_reason, resolution, parent, created, updated, ticket_json) "
        "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            tid,
            str(ticket.type),
            ticket.title,
            str(ticket.status),
            str(ticket.priority),
            ticket.assignee,
            ticket.reporter,
            int(ticket.blocked),
            ticket.blocked_reason,
            str(ticket.resolution) if ticket.resolution is not None else None,
            ticket.parent,
            iso_utc(ticket.created),
            iso_utc(ticket.updated),
            ticket.model_dump_json(),
        ),
    )
    conn.executemany(
        "INSERT INTO ticket_labels(ticket_id, label) VALUES(?, ?)",
        [(tid, label) for label in ticket.labels],
    )
    conn.executemany(
        "INSERT INTO ticket_watchers(ticket_id, handle) VALUES(?, ?)",
        [(tid, handle) for handle in ticket.watchers],
    )
    conn.executemany(
        "INSERT INTO ticket_links(ticket_id, type, host, url, ref) VALUES(?, ?, ?, ?, ?)",
        [
            (
                tid,
                str(link.type),
                str(link.host) if link.host is not None else None,
                link.url,
                link.ref,
            )
            for link in ticket.links
        ],
    )
    comments = "\n".join(c.body for c in ticket.comments)
    conn.execute(
        "INSERT INTO tickets_fts(ticket_id, title, description, comments) VALUES(?, ?, ?, ?)",
        (tid, ticket.title, ticket.description, comments),
    )


def upsert_user(conn: sqlite3.Connection, user: User) -> None:
    """Insert or replace one user-directory row."""
    conn.execute(
        "INSERT OR REPLACE INTO users(handle, name, telegram, gitlab, github, email, account_id) "
        "VALUES(?, ?, ?, ?, ?, ?, ?)",
        (
            user.handle,
            user.name,
            user.telegram,
            user.gitlab,
            user.github,
            user.email,
            user.account_id,
        ),
    )
