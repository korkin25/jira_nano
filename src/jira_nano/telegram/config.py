"""Telegram bot configuration (JN-14).

The bot token and the target forum-supergroup chat id are read from the
environment. The token is a full-access credential and never lives in Git.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from jira_nano.errors import ConfigError

TOKEN_ENV = "TELEGRAM_BOT_TOKEN"
CHAT_ENV = "TELEGRAM_CHAT_ID"


@dataclass(frozen=True)
class TelegramConfig:
    token: str
    chat_id: int | None = None

    @classmethod
    def from_env(cls) -> TelegramConfig:
        """Load the bot config from the environment (``TELEGRAM_BOT_TOKEN`` req.)."""
        token = os.environ.get(TOKEN_ENV)
        if not token:
            raise ConfigError(f"{TOKEN_ENV} is not set")
        chat = os.environ.get(CHAT_ENV)
        return cls(token=token, chat_id=int(chat) if chat else None)
