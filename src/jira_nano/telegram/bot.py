"""aiogram Bot / Dispatcher wiring (JN-14).

The bot is an **internal component**: it calls the service layer in-process
(``JN-D4``) — the service is stored in the dispatcher's workflow data so handlers
can reach it. Mirror behaviour (topics, pings, icons, update posts, comment
pull-back) is added in JN-15..JN-19.
"""
from __future__ import annotations

import os
from pathlib import Path

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message

from jira_nano.service import TicketService
from jira_nano.users import UserDirectory

from .config import TelegramConfig
from .pullback import pull_back


def build_bot(config: TelegramConfig) -> Bot:
    """Create the aiogram Bot from the config (validates the token format)."""
    return Bot(token=config.token)


def build_dispatcher(service: TicketService) -> Dispatcher:
    """Create the Dispatcher with the mirror router and in-process service access."""
    dispatcher = Dispatcher()
    directory = UserDirectory.load(service.paths.config_dir)
    dispatcher["service"] = service
    dispatcher["directory"] = directory
    router = Router(name="jira_nano")

    @router.message()
    async def on_message(message: Message) -> None:
        # JN-19: pull human comments written in Telegram back into ticket files.
        if message.message_thread_id is None or message.text is None or message.from_user is None:
            return
        username = message.from_user.username or str(message.from_user.id)
        pull_back(service, directory, message.message_thread_id, username, message.text)

    dispatcher.include_router(router)
    return dispatcher


def run(repo: Path | None = None) -> None:  # pragma: no cover - bot event loop
    """Console entry point: run the Telegram bot with long polling."""
    import asyncio

    root = Path(repo) if repo is not None else Path(os.environ.get("JIRA_NANO_REPO", "."))
    bot = build_bot(TelegramConfig.from_env())
    dispatcher = build_dispatcher(TicketService(root))
    asyncio.run(dispatcher.start_polling(bot))
