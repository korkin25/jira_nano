"""Parse and serialize ``tickets/JN-<n>.md`` (JN-1 / JN-D3).

Round-trip is stable: ``dumps(loads(text)) == text`` for canonical files.
Frontmatter keys are emitted in a fixed order and conditional keys are omitted
when not applicable (see ``docs/ticket-schema.md``).
"""
from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

import yaml

from .errors import ValidationError
from .models import Comment, Ticket

#: Deterministic frontmatter key order (minimizes diffs).
FRONTMATTER_KEY_ORDER: tuple[str, ...] = (
    "id",
    "type",
    "title",
    "status",
    "priority",
    "assignee",
    "reporter",
    "watchers",
    "labels",
    "blocked",
    "blocked_reason",
    "resolution",
    "parent",
    "links",
    "created",
    "updated",
)

_FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
_COMMENTS_SPLIT_RE = re.compile(r"^## Comments[ \t]*$", re.MULTILINE)
_DESCRIPTION_RE = re.compile(r"\A\s*## Description[ \t]*\n", re.DOTALL)
_COMMENT_HEADER_RE = re.compile(r"<!-- c (?P<attrs>.*?) -->")


def iso_utc(dt: datetime) -> str:
    """Format a datetime as ISO-8601 UTC with a ``Z`` suffix."""
    if dt.tzinfo is not None:
        dt = dt.astimezone(UTC).replace(tzinfo=None)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_dt(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)


def _link_dict(link: Any) -> dict[str, str]:
    d: dict[str, str] = {"type": str(link.type)}
    if link.host is not None:
        d["host"] = str(link.host)
    d["url"] = link.url
    if link.ref is not None:
        d["ref"] = link.ref
    return d


def _frontmatter(ticket: Ticket) -> dict[str, Any]:
    fm: dict[str, Any] = {
        "id": ticket.id,
        "type": str(ticket.type),
        "title": ticket.title,
        "status": str(ticket.status),
        "priority": str(ticket.priority),
        "assignee": ticket.assignee,
        "reporter": ticket.reporter,
        "watchers": list(ticket.watchers),
        "labels": list(ticket.labels),
        "blocked": ticket.blocked,
    }
    if ticket.blocked_reason is not None:
        fm["blocked_reason"] = ticket.blocked_reason
    if ticket.resolution is not None:
        fm["resolution"] = str(ticket.resolution)
    if ticket.parent is not None:
        fm["parent"] = ticket.parent
    fm["links"] = [_link_dict(link) for link in ticket.links]
    fm["created"] = iso_utc(ticket.created)
    fm["updated"] = iso_utc(ticket.updated)
    return fm


def dumps(ticket: Ticket) -> str:
    """Serialize a :class:`Ticket` to markdown (fixed key order, presence rules)."""
    fm_yaml = yaml.safe_dump(
        _frontmatter(ticket),
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        width=10**9,
    )
    doc = f"---\n{fm_yaml}---\n\n## Description\n\n{ticket.description.strip()}\n"
    if ticket.comments:
        blocks = []
        for c in ticket.comments:
            header = f"<!-- c id={c.id} author={c.author} source={c.source} at={iso_utc(c.at)}"
            if c.edited is not None:
                header += f" edited={iso_utc(c.edited)}"
            header += " -->"
            blocks.append(f"{header}\n{c.body.strip()}")
        doc += "\n## Comments\n\n" + "\n\n".join(blocks) + "\n"
    return doc


def _parse_attrs(raw: str) -> dict[str, str]:
    return dict(token.split("=", 1) for token in raw.split())


def _parse_comments(text: str) -> list[Comment]:
    matches = list(_COMMENT_HEADER_RE.finditer(text))
    comments: list[Comment] = []
    for i, match in enumerate(matches):
        attrs = _parse_attrs(match.group("attrs"))
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        comments.append(
            Comment(
                id=int(attrs["id"]),
                author=attrs["author"],
                source=attrs["source"],
                at=_parse_dt(attrs["at"]),
                body=text[match.end() : end].strip(),
                edited=_parse_dt(attrs["edited"]) if "edited" in attrs else None,
            )
        )
    return comments


def loads(text: str) -> Ticket:
    """Parse a ticket markdown document into a :class:`Ticket`."""
    match = _FRONTMATTER_RE.match(text)
    if match is None:
        raise ValidationError("document is missing YAML frontmatter")
    fm: dict[str, Any] = yaml.safe_load(match.group(1)) or {}
    body = text[match.end() :]

    split = _COMMENTS_SPLIT_RE.split(body, maxsplit=1)
    desc_part = split[0]
    comments_part = split[1] if len(split) > 1 else ""
    description = _DESCRIPTION_RE.sub("", desc_part, count=1).strip()
    comments = _parse_comments(comments_part)

    data: dict[str, Any] = dict(fm)
    data["created"] = _parse_dt(fm["created"])
    data["updated"] = _parse_dt(fm["updated"])
    data["description"] = description
    data["comments"] = comments
    return Ticket(**data)
