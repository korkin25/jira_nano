"""Update posts (JN-18).

Formats git change-feed events (JN-35) and posts them into the relevant ticket's
forum topic. Comments that originated in Telegram are skipped to avoid echoing a
human's own message back at them.
"""
from __future__ import annotations

from jira_nano.changefeed import Event
from jira_nano.config import Workflow
from jira_nano.models import Ticket
from jira_nano.service import TicketService

from .format import esc
from .topics import TopicGateway, ensure_topic, header


def render_event(workflow: Workflow, ticket: Ticket, event: Event) -> str:
    """Render a change-feed event as a formatted HTML topic message.

    Layout: a shared header (status icon + bold title + monospace id) followed by
    a one-line summary of the change (``↳ …``); comments quote the body.
    """
    d = event.details
    head = header(workflow, ticket)
    if event.kind == "created":
        return f"{head}\n↳ 🆕 created"
    if event.kind == "status_changed":
        return f"{head}\n↳ {esc(str(d['from']))} → <b>{esc(str(d['to']))}</b>"
    if event.kind == "assignee_changed":
        return f"{head}\n↳ 👤 {esc(str(d['to'])) if d['to'] else 'unassigned'}"
    if event.kind == "blocked_changed":
        return f"{head}\n↳ {'🚫 blocked' if d['blocked'] else '✅ unblocked'}"
    if event.kind == "comment_added":
        who = esc(str(d["author"]))
        body = esc(str(d["body"]))
        return f"{head}\n💬 <b>{who}</b>:\n<blockquote expandable>{body}</blockquote>"
    if event.kind == "link_added":
        label = f"{esc(str(d['type']))} {esc(str(d.get('ref') or ''))}".strip()
        return f'{head}\n↳ 🔗 <a href="{esc(str(d["url"]))}">{label}</a>'
    return f"{head}\n↳ updated"


async def post_events(service: TicketService, gateway: TopicGateway, events: list[Event]) -> None:
    """Post each event into its ticket's topic (skipping Telegram-sourced comments)."""
    for event in events:
        if event.kind == "comment_added" and event.details.get("source") == "telegram":
            continue
        ticket = service.get(event.ticket_id)
        topic_id = await ensure_topic(service, gateway, event.ticket_id)
        await gateway.post_message(topic_id, render_event(service.workflow, ticket, event))
