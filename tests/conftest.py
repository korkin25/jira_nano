"""Shared pytest fixtures."""
from __future__ import annotations

import pytest


class FakeGateway:
    """In-memory stand-in for the Telegram topic gateway (records all calls)."""

    def __init__(self) -> None:
        self.calls: list[str] = []  # created topic names
        self.edits: list[tuple[int, str]] = []  # (topic_id, new name)
        self.posts: list[tuple[int, str]] = []  # (topic_id, text)
        self.cards: list[tuple[int, str]] = []  # (topic_id, caption)
        self._next = 100

    async def create_topic(self, name: str) -> int:
        self.calls.append(name)
        self._next += 1
        return self._next

    async def edit_topic(self, topic_id: int, name: str) -> None:
        self.edits.append((topic_id, name))

    async def post_message(self, topic_id: int, text: str) -> None:
        self.posts.append((topic_id, text))

    async def post_card(self, topic_id: int, image: bytes, caption: str) -> None:
        self.cards.append((topic_id, caption))


@pytest.fixture
def gateway() -> FakeGateway:
    return FakeGateway()
