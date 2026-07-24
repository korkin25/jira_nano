"""MCP server tools — JN-11."""
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


def _names(server: Any) -> set[str]:
    return {t.name for t in asyncio.run(server.list_tools())}


def test_lists_expected_tools(server: Any) -> None:
    assert {
        "jira_create_issue",
        "jira_get_issue",
        "jira_update_issue",
        "jira_search",
        "jira_transition_issue",
        "jira_assign_issue",
        "jira_add_comment",
    } <= _names(server)


def test_create_and_get(server: Any) -> None:
    created = _call(server, "jira_create_issue", {"summary": "Hello", "reporter": "eugeny"})
    assert created["key"] == "JN-1"
    assert created["fields"]["summary"] == "Hello"
    got = _call(server, "jira_get_issue", {"issue_key": "JN-1"})
    assert got["key"] == "JN-1"


def test_get_transitions(server: Any) -> None:
    _call(server, "jira_create_issue", {"summary": "a", "reporter": "e"})
    result = _call(server, "jira_get_transitions", {"issue_key": "JN-1"})
    assert {t["name"] for t in result["transitions"]} == {"in-progress", "archived"}


def test_assign_then_transition(server: Any) -> None:
    _call(server, "jira_create_issue", {"summary": "a", "reporter": "e"})
    _call(server, "jira_assign_issue", {"issue_key": "JN-1", "assignee": "korkin25"})
    moved = _call(server, "jira_transition_issue", {"issue_key": "JN-1", "status": "in-progress"})
    assert moved["fields"]["status"]["name"] == "In Progress"


def test_search_jql(server: Any) -> None:
    _call(server, "jira_create_issue", {"summary": "alpha", "reporter": "e"})
    _call(server, "jira_create_issue", {"summary": "beta", "reporter": "e"})
    results = _call(server, "jira_search", {"jql": "text ~ alpha"})
    assert [r["key"] for r in results["issues"]] == ["JN-1"]
