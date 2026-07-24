"""Skill + MCP wiring — end-to-end agent flow — JN-26."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pygit2
import pytest

from jira_nano.mcp_server import build_server
from jira_nano.service import TicketService


@pytest.fixture
def server(tmp_path: Path) -> Any:
    pygit2.init_repository(str(tmp_path), bare=False)
    return build_server(TicketService(tmp_path))


def _call(server: Any, name: str, args: dict[str, Any]) -> Any:
    out = asyncio.run(server.call_tool(name, args))
    contents = out[0] if isinstance(out, tuple) else out
    return json.loads(contents[0].text)


def test_full_agent_flow(server: Any) -> None:
    created = _call(server, "jira_create_issue", {"summary": "Fix login", "reporter": "eugeny"})
    key = created["key"]
    assert key == "JN-1"

    transitions = _call(server, "jira_get_transitions", {"issue_key": key})
    assert any(t["name"] == "in-progress" for t in transitions["transitions"])

    _call(server, "jira_assign_issue", {"issue_key": key, "assignee": "korkin25"})
    moved = _call(server, "jira_transition_issue", {"issue_key": key, "status": "in-progress"})
    assert moved["fields"]["status"]["name"] == "In Progress"

    _call(server, "jira_add_comment", {"issue_key": key, "body": "on it", "author": "korkin25"})
    got = _call(server, "jira_get_issue", {"issue_key": key})
    assert got["fields"]["comment"]["comments"][-1]["body"] == "on it"

    results = _call(server, "jira_search", {"jql": "status = in-progress"})
    assert [i["key"] for i in results["issues"]] == [key]


def test_mcp_config_example_valid() -> None:
    path = Path(__file__).resolve().parent.parent / "examples" / "mcp.json"
    config = json.loads(path.read_text(encoding="utf-8"))
    assert "jira_nano" in config["mcpServers"]
    assert config["mcpServers"]["jira_nano"]["command"] == "jira-nano-mcp"
