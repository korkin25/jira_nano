"""aiogram Bot / Dispatcher wiring (JN-14).

The bot is an **internal component**: it calls the service layer in-process
(``JN-D4``) — the service is stored in the dispatcher's workflow data so handlers
can reach it. Mirror behaviour (topics, pings, icons, update posts, comment
pull-back) is added in JN-15..JN-19.
"""
from __future__ import annotations

import asyncio
import os
import sys
from io import BytesIO
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message

from jira_nano.service import TicketService
from jira_nano.sync import sync_once
from jira_nano.users import UserDirectory

from .config import TelegramConfig
from .mirror import mirror_since
from .pullback import pull_back
from .topics import BotTopicGateway
from .transcribe import LocalWhisperTranscriber, Transcriber, build_transcriber
from .voice import transcribe_voice


def build_bot(config: TelegramConfig) -> Bot:
    """Create the aiogram Bot from the config (validates the token format)."""
    return Bot(token=config.token)


def build_dispatcher(
    service: TicketService, transcriber: Transcriber | None = None
) -> Dispatcher:
    """Create the Dispatcher with the mirror router and in-process service access.

    ``transcriber`` is the speech-to-text backend for voice pull-back (JN-43). It
    may be ``None``: the backend is then built lazily on the first voice message
    (so the heavy STT libraries are only touched when actually needed).
    """
    dispatcher = Dispatcher()
    directory = UserDirectory.load(service.paths.config_dir)
    dispatcher["service"] = service
    dispatcher["directory"] = directory
    dispatcher["transcriber"] = transcriber
    router = Router(name="jira_nano")

    # JN-43: register the voice handler BEFORE the generic pull-back handler so it
    # wins for voice messages (the generic handler no-ops on them anyway, as
    # ``message.text`` is None, but ordering keeps the intent explicit).
    @router.message(F.voice)
    async def on_voice(message: Message) -> None:  # pragma: no cover - needs live Telegram
        # JN-43: transcribe a voice message and pull it back as a ticket comment.
        if (
            message.message_thread_id is None
            or message.from_user is None
            or message.bot is None
            or message.voice is None
        ):
            return
        active = dispatcher["transcriber"]
        if active is None:
            active = build_transcriber()
            dispatcher["transcriber"] = active
        buf = BytesIO()
        await message.bot.download(message.voice, destination=buf)
        audio = buf.getvalue()
        username = message.from_user.username or str(message.from_user.id)
        # The STT step is CPU-heavy and synchronous: run it off the event loop.
        ticket_id = await asyncio.to_thread(
            transcribe_voice,
            service,
            directory,
            active,
            audio,
            message.voice.mime_type,
            message.message_thread_id,
            username,
        )
        if ticket_id is not None:
            await message.delete()

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
    # JN-44: provision the local Whisper model at startup so the first voice
    # message doesn't wait on the one-time download (the model is cached on disk
    # afterwards). The cloud backend needs nothing; a missing [voice] extra just
    # disables voice instead of crashing the bot.
    transcriber = build_transcriber()
    if isinstance(transcriber, LocalWhisperTranscriber):
        try:
            print("jira_nano: preparing local Whisper model (one-time)…", file=sys.stderr)
            transcriber.ensure_model()
        except RuntimeError as exc:
            print(f"jira_nano: voice transcription disabled — {exc}", file=sys.stderr)
    dispatcher = build_dispatcher(service, transcriber)

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
