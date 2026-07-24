"""Rich read views for the Telegram mirror.

A single-ticket **field card** and a **board/listing**, both wrapping their
structured content in a ``<blockquote>`` so it reads cleanly (the reference
"listing" style). Ticket ids stay monospace so they are easy to copy, dynamic
text is HTML-escaped, and links render as real hyperlinks.
"""
from __future__ import annotations

from collections.abc import Iterable

from jira_nano.config import Workflow
from jira_nano.errors import UnknownHandleError
from jira_nano.models import LinkType, Priority, Ticket
from jira_nano.users import UserDirectory

from .format import esc, ticket_ref
from .topics import status_icon

_PRIORITY = {
    Priority.urgent: "⏫",
    Priority.high: "🔺",
    Priority.medium: "🔸",
    Priority.low: "🔻",
}


def _mention(directory: UserDirectory | None, handle: str) -> str:
    """Resolve a handle to its Telegram ``@mention`` (fallback ``@handle``)."""
    if directory is not None:
        try:
            tg = directory.resolve(handle).telegram
        except UnknownHandleError:
            tg = None
        if tg:
            return esc(tg)
    return esc(f"@{handle}")


def render_ticket(
    workflow: Workflow, ticket: Ticket, directory: UserDirectory | None = None
) -> str:
    """A single-ticket card: title header + a blockquote of key fields."""
    icon = status_icon(workflow, ticket)
    rows = [
        f"<b>id</b> · {ticket_ref(ticket.id)}",
        f"<b>status</b> · {icon} {esc(str(ticket.status))}",
    ]
    if ticket.blocked:
        rows.append("<b>blocked</b> · 🚫")
    assignee = _mention(directory, ticket.assignee) if ticket.assignee else "<i>unassigned</i>"
    rows.append(f"<b>assignee</b> · {assignee}")
    rows.append(f"<b>priority</b> · {_PRIORITY[ticket.priority]} {esc(str(ticket.priority))}")
    for link in ticket.links:
        if link.type is LinkType.telegram:
            continue
        label = esc(link.ref or link.url)
        rows.append(f'<b>{esc(str(link.type))}</b> · <a href="{esc(link.url)}">{label}</a>')
    body = "\n".join(rows)
    return f"{icon} <b>{esc(ticket.title)}</b>\n<blockquote>{body}</blockquote>"


def render_board(
    workflow: Workflow,
    tickets: Iterable[Ticket],
    *,
    title: str = "Board",
    directory: UserDirectory | None = None,
) -> str:
    """A board/sprint listing: header + a numbered blockquote of tickets."""
    items = []
    for i, ticket in enumerate(tickets, 1):
        who = _mention(directory, ticket.assignee) if ticket.assignee else "<i>unassigned</i>"
        icon = status_icon(workflow, ticket)
        items.append(f"{i}. {icon} <b>{ticket_ref(ticket.id)}</b> — {esc(ticket.title)} · {who}")
    listing = "\n".join(items) if items else "<i>empty</i>"
    return f"🗂 <b>{esc(title)}</b>\n<blockquote>{listing}</blockquote>"
