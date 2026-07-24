"""SQLite cache schema (JN-4).

Full-ticket rows (frontmatter + body + comments) so all reads are served from the
cache, plus join tables and an FTS index for text search. A ``meta`` table holds
the schema version and the last-synced commit sha (used by JN-29).
"""
from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 1

# TODO(JN-4): DDL for
#   tickets(id PK, type, title, status, priority, assignee, reporter, blocked,
#           blocked_reason, resolution, parent, created, updated, body, comments_json)
#   ticket_labels(ticket_id, label)
#   ticket_watchers(ticket_id, handle)
#   ticket_links(ticket_id, type, host, url, ref)
#   users(handle PK, name, telegram, gitlab, github, email, account_id)
#   tickets_fts (FTS5 over title + body + comments)
#   meta(schema_version, head_sha)


def create_schema(conn: sqlite3.Connection) -> None:
    """Create all tables/indexes/FTS and stamp the schema version. TODO(JN-4)."""
    raise NotImplementedError


def read_version(conn: sqlite3.Connection) -> int | None:
    """Return the stored schema version, or ``None`` if uninitialized. TODO(JN-4)."""
    raise NotImplementedError
