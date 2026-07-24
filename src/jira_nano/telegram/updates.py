"""Update posts (JN-18).

Formats git change-feed events (JN-35) and posts them into the relevant ticket's
forum topic. Comments that originated in Telegram are skipped to avoid echoing a
human's own message back at them.
"""
from __future__ import annotations

from jira_nano.changefeed import Event
from jira_nano.service import TicketService

from .topics import TopicGateway, ensure_topic


def format_event(event: Event) -> str:
    """Render a change-feed event as a human-readable topic message."""
    d = event.details
    tid = event.ticket_id
    if event.kind == "created":
        return f"{tid}: created ({d['status']})"
    if event.kind == "status_changed":
        return f"{tid}: status {d['from']} → {d['to']}"
    if event.kind == "assignee_changed":
        return f"{tid}: assignee → {d['to'] or 'unassigned'}"
    if event.kind == "blocked_changed":
        return f"{tid}: {'🚫 blocked' if d['blocked'] else 'unblocked'}"
    if event.kind == "comment_added":
        return f"{tid}: 💬 {d['author']}: {d['body']}"
    if event.kind == "link_added":
        return f"{tid}: 🔗 {d['type']} {d['url']}"
    return f"{tid}: updated"


async def post_events(service: TicketService, gateway: TopicGateway, events: list[Event]) -> None:
    """Post each event into its ticket's topic (skipping Telegram-sourced comments)."""
    for event in events:
        if event.kind == "comment_added" and event.details.get("source") == "telegram":
            continue
        topic_id = await ensure_topic(service, gateway, event.ticket_id)
        await gateway.post_message(topic_id, format_event(event))
