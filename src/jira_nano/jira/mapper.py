"""Ticket <-> Jira issue JSON mapping (JN-33 / JN-D5).

Shared by the MCP tools (JN-12) and the HTTP API (JN-13). Supports both dialects:
v2 (plain-string bodies, username-based users) and v3 (ADF bodies, accountId).
Field mapping follows ``docs/http-api.md``; v3 bodies use the Markdown<->ADF
converter (JN-31).
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from jira_nano.errors import UnknownHandleError
from jira_nano.ids import parse_number
from jira_nano.models import Comment, Ticket
from jira_nano.users import UserDirectory

from .adf import adf_to_markdown, markdown_to_adf

#: Jira's "Flagged" impediment custom field.
FLAGGED_FIELD = "customfield_10021"

_STATUS_CATEGORY: dict[str, tuple[str, str]] = {
    "todo": ("new", "To Do"),
    "in-progress": ("indeterminate", "In Progress"),
    "in-review": ("indeterminate", "In Progress"),
    "done": ("done", "Done"),
    "archived": ("done", "Done"),
}
_STATUS_NAME: dict[str, str] = {
    "todo": "To Do",
    "in-progress": "In Progress",
    "in-review": "In Review",
    "done": "Done",
    "archived": "Archived",
}
_ISSUETYPE: dict[str, str] = {"task": "Task", "bug": "Bug", "epic": "Epic"}
_RESOLUTION: dict[str, str] = {
    "wontfix": "Won't Do",
    "duplicate": "Duplicate",
    "obsolete": "Obsolete",
}


def _iso_jira(dt: datetime) -> str:
    dt = dt.astimezone(UTC) if dt.tzinfo is not None else dt.replace(tzinfo=UTC)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000%z")


def _user_ref(
    handle: str | None, version: int, directory: UserDirectory | None
) -> dict[str, Any] | None:
    if handle is None:
        return None
    user = None
    if directory is not None:
        try:
            user = directory.resolve(handle)
        except UnknownHandleError:
            user = None
    display = user.name if user and user.name else handle
    if version >= 3:
        account_id = user.account_id if user and user.account_id else handle
        return {"accountId": account_id, "displayName": display}
    return {"name": handle, "key": handle, "displayName": display}


def _handle_from_ref(ref: dict[str, Any] | None) -> str | None:
    if not ref:
        return None
    handle = ref.get("name") or ref.get("accountId")
    return str(handle) if handle is not None else None


def _comment_json(
    comment: Comment, version: int, directory: UserDirectory | None
) -> dict[str, Any]:
    return {
        "id": str(comment.id),
        "author": _user_ref(comment.author, version, directory),
        "created": _iso_jira(comment.at),
        "body": markdown_to_adf(comment.body) if version >= 3 else comment.body,
    }


def to_jira_issue(
    ticket: Ticket, version: int = 2, directory: UserDirectory | None = None
) -> dict[str, Any]:
    """Render a Ticket as a Jira issue JSON object for the given API version."""
    status = str(ticket.status)
    cat_key, cat_name = _STATUS_CATEGORY[status]
    fields: dict[str, Any] = {
        "summary": ticket.title,
        "description": markdown_to_adf(ticket.description) if version >= 3 else ticket.description,
        "issuetype": {"name": _ISSUETYPE[str(ticket.type)]},
        "status": {
            "name": _STATUS_NAME[status],
            "statusCategory": {"key": cat_key, "name": cat_name},
        },
        "priority": {"name": str(ticket.priority).capitalize()},
        "assignee": _user_ref(ticket.assignee, version, directory),
        "reporter": _user_ref(ticket.reporter, version, directory),
        "labels": list(ticket.labels),
        "created": _iso_jira(ticket.created),
        "updated": _iso_jira(ticket.updated),
        "comment": {"comments": [_comment_json(c, version, directory) for c in ticket.comments]},
    }
    if ticket.parent is not None:
        fields["parent"] = {"key": ticket.parent}
    if ticket.resolution is not None:
        fields["resolution"] = {"name": _RESOLUTION[str(ticket.resolution)]}
    if ticket.blocked:
        fields[FLAGGED_FIELD] = [{"value": "Impediment"}]
    return {"id": str(parse_number(ticket.id)), "key": ticket.id, "fields": fields}


def fields_from_jira(fields: dict[str, Any]) -> dict[str, Any]:
    """Extract jira_nano create/update fields from a Jira issue ``fields`` object."""
    out: dict[str, Any] = {}
    if "summary" in fields:
        out["title"] = fields["summary"]
    if "description" in fields:
        body = fields["description"]
        out["description"] = adf_to_markdown(body) if isinstance(body, dict) else (body or "")
    if fields.get("issuetype"):
        out["type"] = _reverse(_ISSUETYPE, fields["issuetype"].get("name"))
    if fields.get("priority"):
        out["priority"] = str(fields["priority"]["name"]).lower()
    if "assignee" in fields:
        out["assignee"] = _handle_from_ref(fields["assignee"])
    if "labels" in fields:
        out["labels"] = fields["labels"]
    if fields.get("parent"):
        out["parent"] = fields["parent"].get("key")
    return out


def _reverse(mapping: dict[str, str], value: Any) -> str | None:
    for key, name in mapping.items():
        if name == value:
            return key
    return None
