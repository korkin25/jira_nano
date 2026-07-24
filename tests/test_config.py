"""Repo paths and workflow loading — JN-28 / JN-D1."""
from __future__ import annotations

from pathlib import Path

from jira_nano.config import Paths, load_workflow


def test_paths_for_repo(tmp_path: Path) -> None:
    p = Paths.for_repo(tmp_path)
    assert p.root == tmp_path
    assert p.tickets == tmp_path / "tickets"
    assert p.config_dir == tmp_path / ".jira_nano"
    assert p.cache_db.parent == tmp_path / ".jira_nano"


def test_default_workflow(tmp_path: Path) -> None:
    cfg = tmp_path / ".jira_nano"
    cfg.mkdir()
    wf = load_workflow(cfg)
    assert wf.initial == "todo"
    assert wf.transitions["todo"] == ["in-progress", "archived"]
    assert wf.transitions["done"] == ["todo"]
    assert wf.terminal == ["done", "archived"]
    assert wf.guards["in-progress"] == {"require": ["assignee"]}
    assert set(wf.states) == {"todo", "in-progress", "in-review", "done", "archived"}
    assert wf.states["done"]["color"] == "green"
    assert wf.events["mr_merged"] == "done"


def test_workflow_from_file(tmp_path: Path) -> None:
    cfg = tmp_path / ".jira_nano"
    cfg.mkdir()
    (cfg / "workflow.yaml").write_text(
        "workflow:\n"
        "  initial: backlog\n"
        "  states:\n"
        "    - {name: backlog, icon: '🗒️', color: blue}\n"
        "    - {name: done, icon: '✅', color: green}\n"
        "  transitions:\n"
        "    backlog: [done]\n"
        "    done: []\n"
        "  terminal: [done]\n"
        "  guards: {}\n"
        "  events: {}\n"
    )
    wf = load_workflow(cfg)
    assert wf.initial == "backlog"
    assert wf.transitions["backlog"] == ["done"]
    assert set(wf.states) == {"backlog", "done"}
