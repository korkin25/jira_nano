"""SQLite cache schema — JN-4."""
from __future__ import annotations

import sqlite3

from jira_nano.cache.schema import SCHEMA_VERSION, create_schema, read_version


def _names(conn: sqlite3.Connection) -> set[str]:
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master")}


def test_read_version_uninitialized() -> None:
    conn = sqlite3.connect(":memory:")
    assert read_version(conn) is None


def test_create_schema_tables_and_version() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)
    assert {
        "tickets",
        "ticket_labels",
        "ticket_watchers",
        "ticket_links",
        "users",
        "meta",
        "tickets_fts",
    } <= _names(conn)
    assert read_version(conn) == SCHEMA_VERSION


def test_fts_search_works() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)
    conn.execute(
        "INSERT INTO tickets_fts(ticket_id, title, description, comments) "
        "VALUES('JN-1', 'hello world', 'a body', 'a note')"
    )
    rows = conn.execute(
        "SELECT ticket_id FROM tickets_fts WHERE tickets_fts MATCH 'world'"
    ).fetchall()
    assert rows == [("JN-1",)]


def test_create_schema_is_idempotent() -> None:
    conn = sqlite3.connect(":memory:")
    create_schema(conn)
    create_schema(conn)
    assert read_version(conn) == SCHEMA_VERSION
