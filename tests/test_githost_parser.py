"""JN-<n> id parser — JN-20."""
from __future__ import annotations

import pytest

from jira_nano.githost.parser import find_ids


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("JN-42: fix login", ["JN-42"]),
        ("Fixes JN-1 and JN-2", ["JN-1", "JN-2"]),
        ("feature/JN-7-slug", ["JN-7"]),
        ("JN-1 again JN-1", ["JN-1"]),  # deduped
        ("no ids here", []),
        ("JN-42x is not a ref", []),  # word boundary
        ("JN-0 is invalid", []),  # no leading zero / zero
        ("mentions JN-10, JN-2", ["JN-10", "JN-2"]),  # order preserved
    ],
)
def test_find_ids(text: str, expected: list[str]) -> None:
    assert find_ids(text) == expected
