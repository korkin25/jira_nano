"""aiogram Bot / Dispatcher wiring (JN-14).

The bot is an **internal component**: it calls the service layer in-process
(``JN-D4``) — the service is stored in the dispatcher's workflow data so handlers
can reach it. Mirror behaviour (topics, pings, icons, update posts, comment
pull-back) is added in JN-15..JN-19.
"""
from __future__ import annotations

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message

from jira_nano.service import TicketService

from .config import TelegramConfig


def build_bot(config: TelegramConfig) -> Bot:
    """Create the aiogram Bot from the config (validates the token format)."""
    return Bot(token=config.token)


def build_dispatcher(service: TicketService) -> Dispatcher:
    """Create the Dispatcher with the mirror router and in-process service access."""
    dispatcher = Dispatcher()
    dispatcher["service"] = service
    router = Router(name="jira_nano")

    @router.message()
    async def on_message(message: Message) -> None:
        # JN-19: pull human comments written in Telegram back into ticket files.
        return None

    dispatcher.include_router(router)
    return dispatcher
