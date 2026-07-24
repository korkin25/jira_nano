"""Forum topic management (JN-15).

One forum topic per ticket (and epic). The ticket <-> topic mapping is stored as
a ``telegram`` ``links[]`` entry on the ticket (``ref`` = topic id), so it is
versioned in Git and travels with the ticket. The Telegram Bot API call is hidden
behind :class:`TopicGateway` so the logic is testable without Telegram.
"""
from __future__ import annotations

from typing import Protocol

from aiogram import Bot

from jira_nano.config import Workflow
from jira_nano.models import Link, LinkType, Ticket
from jira_nano.service import TicketService

from .format import PARSE_MODE, esc, ticket_ref


class TopicGateway(Protocol):
    async def create_topic(self, name: str) -> int:
        """Create a forum topic and return its ``message_thread_id``."""
        ...

    async def edit_topic(self, topic_id: int, name: str) -> None:
        """Rename an existing forum topic (reflects status/blocked, JN-17)."""
        ...

    async def post_message(self, topic_id: int, text: str) -> None:
        """Post a message into a forum topic (pings, update posts; JN-16/JN-18)."""
        ...


class BotTopicGateway:
    """A :class:`TopicGateway` backed by an aiogram Bot + forum supergroup."""

    def __init__(self, bot: Bot, chat_id: int) -> None:
        self.bot = bot
        self.chat_id = chat_id

    async def create_topic(self, name: str) -> int:
        topic = await self.bot.create_forum_topic(chat_id=self.chat_id, name=name)
        return topic.message_thread_id

    async def edit_topic(self, topic_id: int, name: str) -> None:
        await self.bot.edit_forum_topic(
            chat_id=self.chat_id, message_thread_id=topic_id, name=name
        )

    async def post_message(self, topic_id: int, text: str) -> None:
        await self.bot.send_message(
            chat_id=self.chat_id, message_thread_id=topic_id, text=text, parse_mode=PARSE_MODE
        )


def topic_name(ticket: Ticket) -> str:
    return f"{ticket.id}: {ticket.title}"


def status_icon(workflow: Workflow, ticket: Ticket) -> str:
    """The workflow icon for the ticket's current status (empty if none)."""
    return str(workflow.states.get(str(ticket.status), {}).get("icon", ""))


def topic_title(workflow: Workflow, ticket: Ticket) -> str:
    """Topic title reflecting status (icon) + blocked flag (JN-17 / JN-D1)."""
    blocked = "🚫" if ticket.blocked else ""
    return f"{status_icon(workflow, ticket)}{blocked} {ticket.id}: {ticket.title}".strip()


def header(workflow: Workflow, ticket: Ticket) -> str:
    """Shared HTML message header: status icon + bold title + monospace id."""
    return f"{status_icon(workflow, ticket)} <b>{esc(ticket.title)}</b> {ticket_ref(ticket.id)}"


def topic_color(workflow: Workflow, ticket: Ticket) -> str | None:
    """The Telegram topic colour for the ticket's status (set at creation)."""
    color = workflow.states.get(str(ticket.status), {}).get("color")
    return str(color) if color is not None else None


def topic_id_of(links: list[Link]) -> int | None:
    """Return the mapped forum-topic id from a ticket's links, if any."""
    for link in links:
        if link.type is LinkType.telegram and link.ref:
            return int(link.ref)
    return None


async def ensure_topic(service: TicketService, gateway: TopicGateway, ticket_id: str) -> int:
    """Return the ticket's forum topic id, creating and persisting it if absent."""
    ticket = service.get(ticket_id)
    existing = topic_id_of(ticket.links)
    if existing is not None:
        return existing
    topic_id = await gateway.create_topic(topic_name(ticket))
    service.add_link(
        ticket_id, type="telegram", url=f"tg://forum_topic/{topic_id}", ref=str(topic_id)
    )
    return topic_id


async def refresh_topic(service: TicketService, gateway: TopicGateway, ticket_id: str) -> int:
    """Ensure the ticket's topic exists and rename it to reflect status/blocked."""
    topic_id = await ensure_topic(service, gateway, ticket_id)
    ticket = service.get(ticket_id)
    await gateway.edit_topic(topic_id, topic_title(service.workflow, ticket))
    return topic_id
