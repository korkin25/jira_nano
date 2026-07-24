"""Comment pull-back (JN-19).

A human message written in a ticket's forum topic is written back into the ticket
file as a comment (``source=telegram``), so the Git store stays the single source
of record. The Telegram username is resolved to a canonical handle via the user
directory (falling back to the raw username).
"""
from __future__ import annotations

from jira_nano.service import TicketService
from jira_nano.users import UserDirectory

from .topics import topic_id_of


def find_ticket_by_topic(service: TicketService, topic_id: int) -> str | None:
    """Return the ticket id mapped to a forum topic, if any."""
    for ticket in service.list_tickets():
        if topic_id_of(ticket.links) == topic_id:
            return ticket.id
    return None


def pull_back(
    service: TicketService,
    directory: UserDirectory,
    topic_id: int,
    telegram_username: str,
    text: str,
) -> str | None:
    """Append a Telegram message to its ticket as a comment; return the ticket id."""
    ticket_id = find_ticket_by_topic(service, topic_id)
    if ticket_id is None:
        return None
    user = directory.by_telegram(telegram_username)
    author = user.handle if user is not None else telegram_username.lstrip("@")
    service.comment(ticket_id, author=author, body=text, source="telegram")
    return ticket_id
