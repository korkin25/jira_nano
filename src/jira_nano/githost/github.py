"""GitHub payload parser (JN-22).

Symmetric to :mod:`jira_nano.githost.gitlab`: normalizes GitHub pull-request and
push webhook payloads into a :class:`GitHostEvent`.
"""
from __future__ import annotations

from typing import Any

from .parser import find_ids
from .webhook import GitHostEvent


def parse_github(payload: dict[str, Any]) -> GitHostEvent | None:
    """Parse a GitHub webhook payload into a normalized event (or ``None``)."""
    pull = payload.get("pull_request")
    if pull is not None:
        action = payload.get("action")
        if action == "closed":
            kind = "pr_merged" if pull.get("merged") else "pr_closed"
        elif action in ("opened", "reopened"):
            kind = "pr_opened"
        else:
            return None
        number = pull.get("number")
        return GitHostEvent(
            host="github",
            kind=kind,
            ids=find_ids(pull.get("title", "")),
            ref=f"#{number}" if number is not None else None,
            url=pull.get("html_url"),
            author=(pull.get("user") or {}).get("login"),
        )
    if "commits" in payload and payload.get("ref"):
        ids: list[str] = []
        for commit in payload.get("commits", []):
            for tid in find_ids(commit.get("message", "")):
                if tid not in ids:
                    ids.append(tid)
        first = (payload.get("commits") or [{}])[0]
        return GitHostEvent(
            host="github", kind="push", ids=ids, url=first.get("url"),
            author=(payload.get("sender") or {}).get("login"),
        )
    return None
