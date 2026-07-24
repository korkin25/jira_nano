"""User directory + identity resolution (JN-28 / JN-D3).

``.jira_nano/users.yaml`` is the git source of record; it is mirrored into the
SQLite cache for fast lookup. Tickets reference canonical handles that must
resolve here; the platform ids below drive Telegram pings and git-host matching.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

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
        """Load ``.jira_nano/users.yaml`` (empty directory if the file is absent)."""
        path = config_dir / "users.yaml"
        if not path.exists():
            return cls({})
        raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        users = {
            handle: User(
                handle=handle,
                name=(fields or {}).get("name"),
                telegram=(fields or {}).get("telegram"),
                gitlab=(fields or {}).get("gitlab"),
                github=(fields or {}).get("github"),
                email=(fields or {}).get("email"),
                account_id=(fields or {}).get("account_id"),
            )
            for handle, fields in raw.items()
        }
        return cls(users)

    def resolve(self, handle: str) -> User:
        """Return the user for a handle or raise :class:`UnknownHandleError`."""
        try:
            return self._users[handle]
        except KeyError as exc:  # pragma: no cover - trivial
            raise UnknownHandleError(handle) from exc

    def all_users(self) -> list[User]:
        """Return every user in the directory."""
        return list(self._users.values())

    def by_telegram(self, username: str) -> User | None:
        """Find a user by their Telegram username (``@`` and case insensitive)."""
        target = username.lstrip("@").lower()
        for user in self._users.values():
            if user.telegram and user.telegram.lstrip("@").lower() == target:
                return user
        return None
