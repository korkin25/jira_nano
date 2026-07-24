"""Repository paths and the workflow model (JN-28 / JN-D1).

Loads ``.jira_nano/workflow.yaml`` (falling back to a built-in default) and
resolves the repo layout. The strict transition engine is Phase 2 (JN-10); here
we only load and expose the configured states/transitions/guards.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Paths:
    """Resolved repository paths."""

    root: Path
    tickets: Path  # <root>/tickets/
    config_dir: Path  # <root>/.jira_nano/
    cache_db: Path  # local, .gitignore'd

    @classmethod
    def for_repo(cls, root: Path) -> Paths:
        """Derive the standard paths under a repo root. TODO(JN-28)."""
        raise NotImplementedError


@dataclass(frozen=True)
class Workflow:
    """Configured states, transitions, guards, icons/colors (JN-D1)."""

    initial: str
    states: dict[str, Any]
    transitions: dict[str, list[str]]
    terminal: list[str]
    guards: dict[str, Any]
    events: dict[str, str]


def load_workflow(config_dir: Path) -> Workflow:
    """Load ``workflow.yaml`` or the built-in default (JN-D1). TODO(JN-28)."""
    raise NotImplementedError
