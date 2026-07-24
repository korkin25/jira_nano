"""aiogram Bot / Dispatcher wiring (JN-14).

The bot is an **internal component**: it calls the service layer in-process
(``JN-D4``) — the service is stored in the dispatcher's workflow data so handlers
can reach it. Mirror behaviour (topics, pings, icons, update posts, comment
pull-back) is added in JN-15..JN-19.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher, Router
from aiogram.types import Message

from jira_nano.service import TicketService
from jira_nano.sync import sync_once
from jira_nano.users import UserDirectory

from .config import TelegramConfig
from .mirror import mirror_since
from .pullback import pull_back
from .topics import BotTopicGateway


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
    """Console entry point: run the bot (dispatcher polling + change-feed mirror).

    The aiogram dispatcher (which pulls human comments back from Telegram) and a
    background poller (which mirrors committed ticket changes out to Telegram) run
    concurrently. The mirror needs a target chat, so it is skipped when
    ``TELEGRAM_CHAT_ID`` is unset — the dispatcher still runs on its own.
    """
    import asyncio

    root = Path(repo) if repo is not None else Path(os.environ.get("JIRA_NANO_REPO", "."))
    config = TelegramConfig.from_env()
    bot = build_bot(config)
    service = TicketService(root)
    directory = UserDirectory.load(service.paths.config_dir)
    dispatcher = build_dispatcher(service)

    async def _main() -> None:
        if config.chat_id is None:
            print(
                "jira_nano: Telegram mirror disabled (TELEGRAM_CHAT_ID is not set)",
                file=sys.stderr,
            )
            await dispatcher.start_polling(bot)
            return
        gateway = BotTopicGateway(bot, config.chat_id)
        interval = float(os.environ.get("JIRA_NANO_MIRROR_INTERVAL", "3.0"))

        async def _poll() -> None:
            while True:
                # Refresh the cache first so ``service.get`` sees fresh data.
                sync_once(root)
                await mirror_since(service, gateway, directory)
                await asyncio.sleep(interval)

        await asyncio.gather(dispatcher.start_polling(bot), _poll())

    asyncio.run(_main())
