"""Link writer (JN-23).

Adds a commit / MR / PR link to a ticket's ``links[]`` via the service, skipping
duplicates so replays of the same webhook are idempotent.
"""
from __future__ import annotations

from jira_nano.models import Ticket
from jira_nano.service import TicketService


def link_ticket(
    service: TicketService,
    ticket_id: str,
    *,
    type: str,
    host: str,
    url: str,
    ref: str | None = None,
) -> Ticket:
    """Append a git-host link to the ticket (no-op if the same link is present)."""
    ticket = service.get(ticket_id)
    for link in ticket.links:
        if str(link.type) == type and link.url == url:
            return ticket
    return service.add_link(ticket_id, type=type, host=host, url=url, ref=ref)
