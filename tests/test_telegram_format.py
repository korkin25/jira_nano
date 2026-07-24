"""Telegram message formatting — monospace ticket ids + HTML escaping."""
from __future__ import annotations

import asyncio
from typing import Any, cast

from aiogram import Bot

from jira_nano.telegram.format import PARSE_MODE, esc, ticket_ref
from jira_nano.telegram.topics import BotTopicGateway


def test_ticket_ref_is_monospace() -> None:
    assert ticket_ref("JN-1") == "<code>JN-1</code>"


def test_esc_escapes_html() -> None:
    assert esc("a <b> & c") == "a &lt;b&gt; &amp; c"


def test_bot_gateway_posts_html() -> None:
    class FakeBot:
        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []

        async def send_message(self, **kwargs: Any) -> None:
            self.calls.append(kwargs)

    bot = FakeBot()
    gateway = BotTopicGateway(cast(Bot, bot), chat_id=42)
    asyncio.run(gateway.post_message(7, "hi"))
    assert bot.calls[0]["parse_mode"] == PARSE_MODE
    assert bot.calls[0]["message_thread_id"] == 7
    assert bot.calls[0]["chat_id"] == 42
