"""Polling fallback (JN-37).

Where webhooks are unavailable, poll the host API for recent MRs/PRs/commits and
run each through the same pipeline as the receiver (:func:`dispatch`). A ``seen``
set makes repeated polls idempotent. The fetch is injected so the logic is
testable without a live host.
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from jira_nano.service import TicketService

from .webhook import GitHostEvent, Parser, dispatch

Fetcher = Callable[[], list[dict[str, Any]]]
EventKey = tuple[str, str, str, tuple[str, ...]]


def event_key(event: GitHostEvent) -> EventKey:
    return (event.host, event.kind, event.ref or "", tuple(event.ids))


def poll_once(
    service: TicketService, fetcher: Fetcher, parser: Parser, seen: set[EventKey]
) -> int:
    """Fetch, parse, and dispatch new events; return how many were processed."""
    processed = 0
    for payload in fetcher():
        event = parser(payload)
        if event is None:
            continue
        key = event_key(event)
        if key in seen:
            continue
        seen.add(key)
        dispatch(service, event)
        processed += 1
    return processed
