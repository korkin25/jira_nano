"""Command-line interface — JN-38."""
from __future__ import annotations

from pathlib import Path

import pygit2
import pytest

from jira_nano.cli import main


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    pygit2.init_repository(str(tmp_path), bare=False)
    return tmp_path


def _run(repo: Path, *args: str) -> int:
    return main(["--repo", str(repo), *args])


def test_create_and_get(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert _run(repo, "create", "--title", "Fix login", "--reporter", "eugeny") == 0
    assert capsys.readouterr().out.strip() == "JN-1"
    assert _run(repo, "get", "JN-1") == 0
    assert '"summary"' not in capsys.readouterr().out  # model_dump uses domain field names
    assert _run(repo, "get", "JN-1") == 0
    assert '"title": "Fix login"' in capsys.readouterr().out


def test_list_and_search(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _run(repo, "create", "--title", "alpha", "--reporter", "e")
    _run(repo, "create", "--title", "beta", "--reporter", "e")
    capsys.readouterr()
    _run(repo, "list")
    listed = capsys.readouterr().out
    assert "JN-1" in listed and "JN-2" in listed
    _run(repo, "search", "text ~ alpha")
    assert "JN-1" in capsys.readouterr().out


def test_assign_transition_board(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _run(repo, "create", "--title", "x", "--reporter", "e")
    capsys.readouterr()
    assert _run(repo, "assign", "JN-1", "korkin25") == 0
    capsys.readouterr()
    assert _run(repo, "transition", "JN-1", "in-progress") == 0
    assert capsys.readouterr().out.strip() == "in-progress"
    _run(repo, "board")
    assert "in-progress" in capsys.readouterr().out


def test_illegal_transition_returns_error(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _run(repo, "create", "--title", "x", "--reporter", "e")
    capsys.readouterr()
    assert _run(repo, "transition", "JN-1", "done") == 1
    assert "error:" in capsys.readouterr().err


def test_comment(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _run(repo, "create", "--title", "x", "--reporter", "e")
    capsys.readouterr()
    assert _run(repo, "comment", "JN-1", "--author", "korkin25", "--body", "on it") == 0
    _run(repo, "get", "JN-1")
    assert "on it" in capsys.readouterr().out
