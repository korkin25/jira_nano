"""User directory loading + resolution — JN-28 / JN-D3."""
from __future__ import annotations

from pathlib import Path

import pytest

from jira_nano.errors import UnknownHandleError
from jira_nano.users import UserDirectory


def _write_users(cfg: Path) -> None:
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "users.yaml").write_text(
        "korkin25:\n"
        "  name: Kirill Korkin\n"
        "  telegram: '@korkin25'\n"
        "  gitlab: korkin25\n"
        "  github: korkin\n"
    )


def test_load_and_resolve(tmp_path: Path) -> None:
    cfg = tmp_path / ".jira_nano"
    _write_users(cfg)
    directory = UserDirectory.load(cfg)
    user = directory.resolve("korkin25")
    assert user.handle == "korkin25"
    assert user.name == "Kirill Korkin"
    assert user.telegram == "@korkin25"
    assert user.github == "korkin"
    assert user.email is None


def test_resolve_unknown(tmp_path: Path) -> None:
    cfg = tmp_path / ".jira_nano"
    _write_users(cfg)
    directory = UserDirectory.load(cfg)
    with pytest.raises(UnknownHandleError):
        directory.resolve("nobody")


def test_missing_file_is_empty(tmp_path: Path) -> None:
    cfg = tmp_path / ".jira_nano"
    cfg.mkdir()
    directory = UserDirectory.load(cfg)
    with pytest.raises(UnknownHandleError):
        directory.resolve("anyone")
