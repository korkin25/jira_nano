"""Sequential ticket id allocation — JN-3."""
from __future__ import annotations

from pathlib import Path

import pytest

from jira_nano.ids import allocate, parse_number


def _touch(tickets: Path, *ids: str) -> None:
    tickets.mkdir(parents=True, exist_ok=True)
    for tid in ids:
        (tickets / f"{tid}.md").write_text("x", encoding="utf-8")


def test_allocate_on_missing_dir(tmp_path: Path) -> None:
    assert allocate(tmp_path / "tickets") == "JN-1"


def test_allocate_sequential(tmp_path: Path) -> None:
    tickets = tmp_path / "tickets"
    _touch(tickets, "JN-1", "JN-2")
    assert allocate(tickets) == "JN-3"


def test_allocate_never_reuses_gaps(tmp_path: Path) -> None:
    tickets = tmp_path / "tickets"
    _touch(tickets, "JN-1", "JN-3")  # JN-2 retired
    assert allocate(tickets) == "JN-4"


def test_parse_number() -> None:
    assert parse_number("JN-42") == 42
    assert parse_number("JN-1") == 1


@pytest.mark.parametrize("bad", ["J-1", "JN-0", "JN-01", "42", "JN-", "jn-1"])
def test_parse_number_invalid(bad: str) -> None:
    with pytest.raises(ValueError):
        parse_number(bad)
