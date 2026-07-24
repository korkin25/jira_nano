"""Assignment pings (JN-16).

When a ticket is assigned, post a message into its forum topic that ``@mention``s
the assignee. The Telegram handle comes from the user directory
(``.jira_nano/users.yaml``); if the handle is not in the directory, fall back to a
plain ``@handle`` mention.
"""
from __future__ import annotations

from jira_nano.errors import UnknownHandleError
from jira_nano.service import TicketService
from jira_nano.users import UserDirectory

from .format import esc
from .topics import TopicGateway, ensure_topic, header


async def ping_assignee(
    service: TicketService,
    gateway: TopicGateway,
    directory: UserDirectory,
    ticket_id: str,
) -> None:
    """Post an assignment ping into the ticket's topic (no-op if unassigned)."""
    ticket = service.get(ticket_id)
    if ticket.assignee is None:
        return
    try:
        mention = directory.resolve(ticket.assignee).telegram or f"@{ticket.assignee}"
    except UnknownHandleError:
        mention = f"@{ticket.assignee}"
    topic_id = await ensure_topic(service, gateway, ticket_id)
    text = f"{header(service.workflow, ticket)}\n↳ 👤 assigned to {esc(mention)}"
    await gateway.post_message(topic_id, text)
