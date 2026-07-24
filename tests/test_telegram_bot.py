"""Telegram bot skeleton — JN-14."""
from __future__ import annotations

from pathlib import Path

import pygit2
import pytest
from aiogram import Bot, Dispatcher

from jira_nano.errors import ConfigError
from jira_nano.service import TicketService
from jira_nano.telegram.bot import build_bot, build_dispatcher
from jira_nano.telegram.config import TelegramConfig

_VALID_TOKEN = "123456:AAExampleValidLookingTokenABCDEFGHIJKLMNO"


def test_config_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", _VALID_TOKEN)
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "-1001234567890")
    config = TelegramConfig.from_env()
    assert config.token == _VALID_TOKEN
    assert config.chat_id == -1001234567890


def test_config_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    with pytest.raises(ConfigError):
        TelegramConfig.from_env()


def test_build_bot() -> None:
    bot = build_bot(TelegramConfig(token=_VALID_TOKEN))
    assert isinstance(bot, Bot)
    assert bot.token == _VALID_TOKEN


def test_build_dispatcher_wires_service(tmp_path: Path) -> None:
    pygit2.init_repository(str(tmp_path), bare=False)
    service = TicketService(tmp_path)
    dispatcher = build_dispatcher(service)
    assert isinstance(dispatcher, Dispatcher)
    assert dispatcher["service"] is service
    assert len(dispatcher.sub_routers) == 1
