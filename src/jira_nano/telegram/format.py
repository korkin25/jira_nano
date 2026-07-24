"""Message-body formatting for the Telegram mirror.

Message bodies (assignment pings, update posts) are sent as HTML so the ticket id
can be rendered **monospace** — that makes it easy to copy from Telegram. Any
other dynamic text embedded in a body is HTML-escaped. Forum topic *names* are
plain text (Telegram does not format them) and are not handled here.

``ticket_ref`` is the single place that decides how a ticket id looks in a
message; today it is monospace, later it can become a deep link.
"""
from __future__ import annotations

import html

PARSE_MODE = "HTML"


def ticket_ref(ticket_id: str) -> str:
    """Render a ticket id for a message body (monospace now, a link later)."""
    return f"<code>{html.escape(ticket_id)}</code>"


def esc(text: str) -> str:
    """HTML-escape dynamic text embedded in an HTML message body."""
    return html.escape(text)
