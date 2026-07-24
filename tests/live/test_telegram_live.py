"""End-to-end live test of the Telegram mirror against a real bot + forum group.

Opt-in only: skipped unless ``JIRA_NANO_LIVE=1`` and ``TELEGRAM_BOT_TOKEN`` /
``TELEGRAM_CHAT_ID`` are set, so normal test runs and CI stay green. It creates a
throwaway ticket repo, drives the real mirror code end-to-end against the
configured forum supergroup, and deletes the topic it creates.

Run:  JIRA_NANO_LIVE=1 TELEGRAM_BOT_TOKEN=… TELEGRAM_CHAT_ID=… pytest -m live
Keep the created topic for visual inspection with ``JIRA_NANO_LIVE_KEEP=1``.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pygit2
import pytest
from aiogram import Bot

from jira_nano.changefeed import Event
from jira_nano.service import TicketService
from jira_nano.telegram.config import TelegramConfig
from jira_nano.telegram.pings import ping_assignee
from jira_nano.telegram.topics import BotTopicGateway, refresh_topic, topic_id_of
from jira_nano.telegram.updates import post_events
from jira_nano.telegram.views import render_board, render_ticket
from jira_nano.users import UserDirectory

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        os.environ.get("JIRA_NANO_LIVE") != "1" or not os.environ.get("TELEGRAM_BOT_TOKEN"),
        reason="live test; set JIRA_NANO_LIVE=1 and TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID",
    ),
]


def _repo(root: Path) -> TicketService:
    pygit2.init_repository(str(root), bare=False)
    cfg = root / ".jira_nano"
    cfg.mkdir()
    (cfg / "users.yaml").write_text("me:\n  telegram: '@jira_test_5_bot'\n")
    return TicketService(root)


def test_telegram_mirror_live(tmp_path: Path) -> None:
    """Create a ticket and mirror its whole lifecycle into a real forum topic."""
    svc = _repo(tmp_path)
    directory = UserDirectory.load(svc.paths.config_dir)
    cfg = TelegramConfig.from_env()
    assert cfg.chat_id is not None, "TELEGRAM_CHAT_ID must be set"
    chat_id = cfg.chat_id
    bot = Bot(token=cfg.token)
    gw = BotTopicGateway(bot, chat_id)

    async def run() -> None:
        try:
            assert (await bot.get_me()).username  # token is valid

            ticket = svc.create(title="[live-test] mirror", reporter="me")

            # 1. topic is created and its id persisted on the ticket
            topic_id = await refresh_topic(svc, gw, ticket.id)
            assert isinstance(topic_id, int)
            assert topic_id_of(svc.get(ticket.id).links) == topic_id

            # 2. assign + transition renames the same topic (no new topic)
            svc.assign(ticket.id, "me")
            svc.transition(ticket.id, "in-progress")
            assert await refresh_topic(svc, gw, ticket.id) == topic_id

            # 3. ping, update post and the rich views all send without error
            await ping_assignee(svc, gw, directory, ticket.id)
            await post_events(
                svc, gw,
                [Event("status_changed", ticket.id, {"from": "todo", "to": "in-progress"})],
            )
            card = render_ticket(svc.workflow, svc.get(ticket.id), directory)
            await gw.post_message(topic_id, card)
            await gw.post_message(
                topic_id,
                render_board(svc.workflow, svc.list_tickets(), title="[live-test] board",
                             directory=directory),
            )

            # 4. clean up unless asked to keep it for inspection
            if os.environ.get("JIRA_NANO_LIVE_KEEP") != "1":
                await bot.delete_forum_topic(chat_id=chat_id, message_thread_id=topic_id)
        finally:
            await bot.session.close()

    asyncio.run(run())
