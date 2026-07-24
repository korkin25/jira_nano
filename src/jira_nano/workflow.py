"""Workflow engine — strict transition validation (JN-10 / JN-D1).

The configured workflow (``config.Workflow``) is a strict state machine: only
transitions declared in ``transitions`` are legal, and a target's ``guards`` must
be satisfied. There is **no force/override bypass**.
"""
from __future__ import annotations

from .config import Workflow
from .errors import TransitionError
from .models import Ticket


def legal_transitions(workflow: Workflow, current: str) -> list[str]:
    """Return the target statuses reachable from ``current`` in one step."""
    return list(workflow.transitions.get(current, []))


def check_transition(workflow: Workflow, ticket: Ticket, target: str) -> None:
    """Raise :class:`TransitionError` if ``ticket`` may not move to ``target``."""
    current = str(ticket.status)
    if target not in workflow.transitions.get(current, []):
        raise TransitionError(f"illegal transition {current} -> {target}")
    guard = workflow.guards.get(target)
    if guard:
        for field in guard.get("require", []):
            if not getattr(ticket, field, None):
                raise TransitionError(f"transition to {target} requires {field!r}")
