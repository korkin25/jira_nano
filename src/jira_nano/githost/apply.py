"""Git-host event → workflow transition (JN-24 / JN-D1).

A configured event (``mr_opened`` → ``in-review`` …) names a target status; the
ticket is advanced **forward along the shortest legal transition path** to reach
it. When a step crosses the ``in-progress`` assignee guard on an unassigned
ticket, the MR/PR author is auto-assigned so the guard is satisfied legally. If
the target is unreachable, the event is skipped and a note is posted.
"""
from __future__ import annotations

from collections import deque

from jira_nano.config import Workflow
from jira_nano.models import Ticket
from jira_nano.service import TicketService


def shortest_path(workflow: Workflow, start: str, target: str) -> list[str] | None:
    """Shortest legal transition path from ``start`` to ``target`` (inclusive)."""
    if start == target:
        return [start]
    queue: deque[list[str]] = deque([[start]])
    visited = {start}
    while queue:
        path = queue.popleft()
        for nxt in workflow.transitions.get(path[-1], []):
            if nxt == target:
                return [*path, nxt]
            if nxt not in visited:
                visited.add(nxt)
                queue.append([*path, nxt])
    return None


def apply_event(
    service: TicketService, ticket_id: str, event_kind: str, author: str | None = None
) -> Ticket | None:
    """Advance a ticket to the status mapped to ``event_kind`` (or note/skip)."""
    workflow = service.workflow
    target = workflow.events.get(event_kind)
    if target is None:
        return None  # event not mapped
    current = str(service.get(ticket_id).status)
    path = shortest_path(workflow, current, target)
    if path is None:
        service.comment(
            ticket_id,
            author="githost",
            body=f"git-host event {event_kind}: {target} unreachable from {current}",
            source="githost",
        )
        return None
    for step in path[1:]:
        require = workflow.guards.get(step, {}).get("require", [])
        if "assignee" in require and service.get(ticket_id).assignee is None and author is not None:
            service.assign(ticket_id, author)
        service.transition(ticket_id, step)
    return service.get(ticket_id)
