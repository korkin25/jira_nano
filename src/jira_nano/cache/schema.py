"""SQLite cache schema (JN-4).

Full-ticket rows (frontmatter columns + a ``ticket_json`` blob) so all reads are
served from the cache, plus join tables and an FTS index for text search. A
``meta`` table holds the schema version and the last-synced commit sha (JN-29).
"""
from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 1

_DDL = """
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tickets (
    id             TEXT PRIMARY KEY,
    type           TEXT NOT NULL,
    title          TEXT NOT NULL,
    status         TEXT NOT NULL,
    priority       TEXT NOT NULL,
    assignee       TEXT,
    reporter       TEXT NOT NULL,
    blocked        INTEGER NOT NULL,
    blocked_reason TEXT,
    resolution     TEXT,
    parent         TEXT,
    created        TEXT NOT NULL,
    updated        TEXT NOT NULL,
    ticket_json    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_tickets_status   ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_tickets_assignee ON tickets(assignee);
CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority);
CREATE INDEX IF NOT EXISTS idx_tickets_type     ON tickets(type);
CREATE INDEX IF NOT EXISTS idx_tickets_parent   ON tickets(parent);
CREATE TABLE IF NOT EXISTS ticket_labels (
    ticket_id TEXT NOT NULL,
    label     TEXT NOT NULL,
    PRIMARY KEY (ticket_id, label)
);
CREATE TABLE IF NOT EXISTS ticket_watchers (
    ticket_id TEXT NOT NULL,
    handle    TEXT NOT NULL,
    PRIMARY KEY (ticket_id, handle)
);
CREATE TABLE IF NOT EXISTS ticket_links (
    ticket_id TEXT NOT NULL,
    type      TEXT NOT NULL,
    host      TEXT,
    url       TEXT NOT NULL,
    ref       TEXT
);
CREATE TABLE IF NOT EXISTS users (
    handle     TEXT PRIMARY KEY,
    name       TEXT,
    telegram   TEXT,
    gitlab     TEXT,
    github     TEXT,
    email      TEXT,
    account_id TEXT
);
CREATE VIRTUAL TABLE IF NOT EXISTS tickets_fts USING fts5 (
    ticket_id UNINDEXED,
    title,
    description,
    comments
);
"""


def create_schema(conn: sqlite3.Connection) -> None:
    """Create all tables/indexes/FTS and stamp the schema version. Idempotent."""
    conn.executescript(_DDL)
    conn.execute(
        "INSERT INTO meta(key, value) VALUES('schema_version', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (str(SCHEMA_VERSION),),
    )
    conn.commit()


def read_version(conn: sqlite3.Connection) -> int | None:
    """Return the stored schema version, or ``None`` if uninitialized."""
    try:
        row = conn.execute("SELECT value FROM meta WHERE key = 'schema_version'").fetchone()
    except sqlite3.OperationalError:
        return None
    return int(row[0]) if row else None
