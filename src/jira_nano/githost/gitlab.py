"""GitLab payload parser (JN-21).

Normalizes GitLab webhook payloads (merge-request and push events) into a
:class:`GitHostEvent`. Ticket ids come from the MR title / commit messages.
"""
from __future__ import annotations

from typing import Any

from .parser import collect_commit_ids, find_ids
from .webhook import GitHostEvent

_MR_ACTIONS = {
    "open": "mr_opened",
    "reopen": "mr_opened",
    "merge": "mr_merged",
    "close": "mr_closed",
}


def parse_gitlab(payload: dict[str, Any]) -> GitHostEvent | None:
    """Parse a GitLab webhook payload into a normalized event (or ``None``)."""
    kind = payload.get("object_kind")
    if kind == "merge_request":
        attrs = payload.get("object_attributes", {})
        mapped = _MR_ACTIONS.get(attrs.get("action"))
        if mapped is None:
            return None
        iid = attrs.get("iid")
        return GitHostEvent(
            host="gitlab",
            kind=mapped,
            ids=find_ids(attrs.get("title", "")),
            ref=f"!{iid}" if iid is not None else None,
            url=attrs.get("url"),
            author=(payload.get("user") or {}).get("username"),
        )
    if kind == "push":
        first = (payload.get("commits") or [{}])[0]
        return GitHostEvent(
            host="gitlab",
            kind="push",
            ids=collect_commit_ids(payload.get("commits", [])),
            url=first.get("url"),
            author=payload.get("user_username"),
        )
    return None
