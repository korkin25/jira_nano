"""Detect ``JN-<n>`` ticket ids in text (JN-20).

Used on commit messages, MR/PR titles, and branch names. Matches are bounded so
there are no false positives (``JN-42x`` and ``JN-0`` do not match), and the
result preserves first-seen order without duplicates.
"""
from __future__ import annotations

import re
from typing import Any

_ID_RE = re.compile(r"\bJN-[1-9]\d*\b")


def find_ids(text: str) -> list[str]:
    """Return the distinct ``JN-<n>`` ids referenced in ``text``, in order."""
    found: list[str] = []
    for match in _ID_RE.finditer(text):
        if match.group() not in found:
            found.append(match.group())
    return found


def collect_commit_ids(commits: list[dict[str, Any]]) -> list[str]:
    """Return the distinct ``JN-<n>`` ids across commit messages, first-seen order.

    Shared by the GitLab and GitHub push-event parsers, whose payloads both carry
    a ``commits`` list of ``{"message": ...}`` objects.
    """
    ids: list[str] = []
    for commit in commits:
        for tid in find_ids(commit.get("message", "")):
            if tid not in ids:
                ids.append(tid)
    return ids
