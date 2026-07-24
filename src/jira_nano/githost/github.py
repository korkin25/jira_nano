"""GitHub payload parser (JN-22).

Symmetric to :mod:`jira_nano.githost.gitlab`: normalizes GitHub pull-request and
push webhook payloads into a :class:`GitHostEvent`.
"""
from __future__ import annotations

from typing import Any

from .parser import collect_commit_ids, find_ids
from .webhook import GitHostEvent

_PR_KINDS = {"opened": "pr_opened", "reopened": "pr_opened"}


def _parse_pull_request(pull: dict[str, Any], action: str | None) -> GitHostEvent | None:
    """Normalize a ``pull_request`` payload; ``None`` for unhandled actions."""
    if action == "closed":
        kind = "pr_merged" if pull.get("merged") else "pr_closed"
    else:
        kind = _PR_KINDS.get(action or "", "")
        if not kind:
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


def _parse_push(payload: dict[str, Any]) -> GitHostEvent:
    """Normalize a push payload into a ``push`` event."""
    first = (payload.get("commits") or [{}])[0]
    return GitHostEvent(
        host="github",
        kind="push",
        ids=collect_commit_ids(payload.get("commits", [])),
        url=first.get("url"),
        author=(payload.get("sender") or {}).get("login"),
    )


def parse_github(payload: dict[str, Any]) -> GitHostEvent | None:
    """Parse a GitHub webhook payload into a normalized event (or ``None``)."""
    pull = payload.get("pull_request")
    if pull is not None:
        return _parse_pull_request(pull, payload.get("action"))
    if "commits" in payload and payload.get("ref"):
        return _parse_push(payload)
    return None
