"""Repository paths and the workflow model (JN-28 / JN-D1).

Loads ``.jira_nano/workflow.yaml`` (falling back to a built-in default) and
resolves the repo layout. The strict transition engine is Phase 2 (JN-10); here
we only load and expose the configured states/transitions/guards.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

CONFIG_DIRNAME = ".jira_nano"
TICKETS_DIRNAME = "tickets"


@dataclass(frozen=True)
class Paths:
    """Resolved repository paths."""

    root: Path
    tickets: Path  # <root>/tickets/
    config_dir: Path  # <root>/.jira_nano/
    cache_db: Path  # local, .gitignore'd

    @classmethod
    def for_repo(cls, root: Path) -> Paths:
        """Derive the standard paths under a repo root."""
        root = Path(root)
        config_dir = root / CONFIG_DIRNAME
        return cls(
            root=root,
            tickets=root / TICKETS_DIRNAME,
            config_dir=config_dir,
            cache_db=config_dir / "cache.db",
        )


@dataclass(frozen=True)
class Workflow:
    """Configured states, transitions, guards, icons/colors (JN-D1)."""

    initial: str
    states: dict[str, dict[str, Any]]  # name -> {icon, color, ...}
    transitions: dict[str, list[str]]
    terminal: list[str]
    guards: dict[str, Any]
    events: dict[str, str]


#: Built-in default workflow (docs/status-model.md § Config shape).
DEFAULT_WORKFLOW_RAW: dict[str, Any] = {
    "initial": "todo",
    "states": [
        {"name": "todo", "icon": "📋", "color": "yellow"},
        {"name": "in-progress", "icon": "🔧", "color": "purple"},
        {"name": "in-review", "icon": "👀", "color": "pink"},
        {"name": "done", "icon": "✅", "color": "green"},
        {"name": "archived", "icon": "📦", "color": "red"},
    ],
    "transitions": {
        "todo": ["in-progress", "archived"],
        "in-progress": ["in-review", "todo", "archived"],
        "in-review": ["done", "in-progress", "archived"],
        "done": ["todo"],
        "archived": ["todo"],
    },
    "terminal": ["done", "archived"],
    "guards": {"in-progress": {"require": ["assignee"]}},
    "events": {
        "mr_opened": "in-review",
        "pr_opened": "in-review",
        "mr_merged": "done",
        "pr_merged": "done",
        "mr_closed": "in-progress",
        "pr_closed": "in-progress",
    },
}


def _workflow_from_raw(raw: dict[str, Any]) -> Workflow:
    states = {s["name"]: {k: v for k, v in s.items() if k != "name"} for s in raw["states"]}
    return Workflow(
        initial=raw["initial"],
        states=states,
        transitions=raw["transitions"],
        terminal=raw["terminal"],
        guards=raw.get("guards", {}),
        events=raw.get("events", {}),
    )


DEFAULT_WORKFLOW: Workflow = _workflow_from_raw(DEFAULT_WORKFLOW_RAW)


def default_workflow_yaml() -> str:
    """The built-in default workflow serialized for a fresh ``workflow.yaml``."""
    return yaml.safe_dump({"workflow": DEFAULT_WORKFLOW_RAW}, sort_keys=False, allow_unicode=True)


def load_workflow(config_dir: Path) -> Workflow:
    """Load ``workflow.yaml`` or return the built-in default (JN-D1)."""
    path = config_dir / "workflow.yaml"
    if not path.exists():
        return DEFAULT_WORKFLOW
    raw: dict[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
    return _workflow_from_raw(raw["workflow"])
