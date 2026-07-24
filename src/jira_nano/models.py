"""Domain models for jira_nano tickets (JN-1 / JN-D3).

The canonical schema is ``docs/ticket-schema.md``. Cross-field rules
(``blocked_reason`` iff ``blocked``, ``resolution`` iff ``archived``, id format,
``updated >= created``) are enforced by validators added under JN-1.
"""
from __future__ import annotations

import re
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

#: A valid ticket id: ``JN-`` followed by a positive integer with no leading zero.
ID_RE = re.compile(r"^JN-[1-9]\d*$")


class Status(StrEnum):
    todo = "todo"
    in_progress = "in-progress"
    in_review = "in-review"
    done = "done"
    archived = "archived"


class Type(StrEnum):
    task = "task"
    bug = "bug"
    epic = "epic"


class Priority(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class Resolution(StrEnum):
    wontfix = "wontfix"
    duplicate = "duplicate"
    obsolete = "obsolete"


class LinkType(StrEnum):
    commit = "commit"
    mr = "mr"
    pr = "pr"
    branch = "branch"
    issue = "issue"
    telegram = "telegram"  # ticket <-> forum-topic mapping (JN-15)


class Host(StrEnum):
    gitlab = "gitlab"
    github = "github"


class Link(BaseModel):
    type: LinkType
    host: Host | None = None
    url: str
    ref: str | None = None


class Comment(BaseModel):
    """One HTML-comment-delimited entry from the ``## Comments`` log."""

    id: int
    author: str
    source: str  # telegram | mcp | api | githost
    at: datetime
    body: str
    edited: datetime | None = None


class Ticket(BaseModel):
    """A single ticket (``tickets/JN-<n>.md``): frontmatter + body."""

    id: str
    type: Type = Type.task
    title: str
    status: Status = Status.todo
    priority: Priority = Priority.medium
    assignee: str | None = None
    reporter: str
    watchers: list[str] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    blocked: bool = False
    blocked_reason: str | None = None
    resolution: Resolution | None = None
    parent: str | None = None
    links: list[Link] = Field(default_factory=list)
    created: datetime
    updated: datetime
    # Body (Markdown):
    description: str = ""
    comments: list[Comment] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_consistency(self) -> Ticket:
        """Enforce the presence/consistency rules of docs/ticket-schema.md."""
        if not ID_RE.match(self.id):
            raise ValueError(f"invalid ticket id: {self.id!r}")
        if self.parent is not None and not ID_RE.match(self.parent):
            raise ValueError(f"invalid parent id: {self.parent!r}")
        if self.blocked_reason is not None and not self.blocked:
            raise ValueError("blocked_reason is set but blocked is false")
        if self.resolution is not None and self.status is not Status.archived:
            raise ValueError("resolution is only allowed on archived tickets")
        if self.updated < self.created:
            raise ValueError("updated is before created")
        return self
