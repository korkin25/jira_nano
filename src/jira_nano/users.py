"""User directory + identity resolution (JN-28 / JN-D3).

``.jira_nano/users.yaml`` is the git source of record; it is mirrored into the
SQLite cache for fast lookup. Tickets reference canonical handles that must
resolve here; the platform ids below drive Telegram pings and git-host matching.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .errors import UnknownHandleError


@dataclass(frozen=True)
class User:
    handle: str
    name: str | None = None
    telegram: str | None = None
    gitlab: str | None = None
    github: str | None = None
    email: str | None = None
    account_id: str | None = None  # Jira REST v3 accountId (JN-D5); default: handle


class UserDirectory:
    """The loaded ``users.yaml``, keyed by canonical handle."""

    def __init__(self, users: dict[str, User]) -> None:
        self._users = users

    @classmethod
    def load(cls, config_dir: Path) -> UserDirectory:
        """Load ``.jira_nano/users.yaml``. TODO(JN-28)."""
        raise NotImplementedError

    def resolve(self, handle: str) -> User:
        """Return the user for a handle or raise :class:`UnknownHandleError`."""
        try:
            return self._users[handle]
        except KeyError as exc:  # pragma: no cover - trivial
            raise UnknownHandleError(handle) from exc
