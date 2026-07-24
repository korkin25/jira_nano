"""Telegram auto-trigger — mirror committed ticket changes into Telegram (JN-16/JN-18/JN-35).

The bot's background poller advances a cursor over Git history and turns each new
committed change into the right Telegram side effect: assignment pings, forum-topic
renames (status/blocked), and update posts. The cursor lives in the cache ``meta``
table under ``telegram_head_sha`` — kept **separate** from the sync cursor
(``head_sha``, JN-29) so cache refresh and Telegram mirroring advance independently.

The first run records a baseline (it does not replay pre-existing history); a
rewritten history that makes the stored sha unresolvable re-baselines rather than
raising, so the poller is self-healing.
"""
from __future__ import annotations

import sqlite3
from typing import Any

import pygit2

from jira_nano.changefeed import Event, changes_between
from jira_nano.service import TicketService
from jira_nano.users import UserDirectory

from .pings import ping_assignee
from .topics import TopicGateway, refresh_topic
from .updates import post_events

_CURSOR_KEY = "telegram_head_sha"

#: Kinds whose forum-topic title must be re-synced (status icon / blocked flag).
_REFRESH_KINDS = {"created", "status_changed", "blocked_changed"}


async def dispatch_events(
    service: TicketService,
    gateway: TopicGateway,
    directory: UserDirectory,
    events: list[Event],
) -> None:
    """Mirror a batch of change-feed events into Telegram, in order.

    Assignment changes post a single ``@mention`` ping (never an extra update
    line); status/blocked/created changes first re-sync the topic title, then all
    other kinds fall through to a normal update post.
    """
    for event in events:
        if event.kind == "assignee_changed":
            if event.details.get("to"):
                await ping_assignee(service, gateway, directory, event.ticket_id)
            continue
        if event.kind in _REFRESH_KINDS:
            await refresh_topic(service, gateway, event.ticket_id)
        await post_events(service, gateway, [event])


def read_cursor(conn: sqlite3.Connection) -> str | None:
    """Return the stored Telegram mirror cursor sha, or ``None`` if unset."""
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (_CURSOR_KEY,)).fetchone()
    return row[0] if row else None


def write_cursor(conn: sqlite3.Connection, sha: str) -> None:
    """Store ``sha`` as the Telegram mirror cursor (upsert)."""
    conn.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (_CURSOR_KEY, sha),
    )


async def mirror_since(
    service: TicketService,
    gateway: TopicGateway,
    directory: UserDirectory,
) -> str | None:
    """Mirror every committed change since the stored cursor; advance the cursor.

    Returns the new cursor sha (repo ``HEAD``), or ``None`` when the repo has no
    commits yet. The first ever call baselines the cursor without replaying
    history; an unresolvable stored sha (history rewrite) re-baselines instead of
    raising.
    """
    repo: Any = pygit2.Repository(str(service.paths.root))
    current = None if repo.head_is_unborn else str(repo.head.target)
    if current is None:
        return None
    stored = read_cursor(service.conn)
    if stored is None:
        write_cursor(service.conn, current)
        service.conn.commit()
        return current
    if stored == current:
        return current
    try:
        events = changes_between(service.paths.root, stored, current)
    except Exception:
        # Stored sha no longer resolves (e.g. history rewrite) — re-baseline.
        write_cursor(service.conn, current)
        service.conn.commit()
        return current
    await dispatch_events(service, gateway, directory, events)
    write_cursor(service.conn, current)
    service.conn.commit()
    return current
