"""MCP tool-shape conformance with common Jira MCP servers — JN-12."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import pygit2
import pytest

from jira_nano.mcp_server import build_server
from jira_nano.service import TicketService

EXPECTED_TOOLS = {
    "jira_create_issue",
    "jira_get_issue",
    "jira_update_issue",
    "jira_delete_issue",
    "jira_batch_create_issues",
    "jira_search",
    "jira_get_project_issues",
    "jira_get_transitions",
    "jira_transition_issue",
    "jira_assign_issue",
    "jira_add_comment",
    "jira_edit_comment",
    "jira_add_watcher",
    "jira_remove_watcher",
    "jira_get_issue_watchers",
    "jira_link_to_epic",
    "jira_create_remote_issue_link",
    "jira_get_user_profile",
    "jira_search_assignable_users",
}


@pytest.fixture
def server(tmp_path: Path) -> Any:
    pygit2.init_repository(str(tmp_path), bare=False)
    cfg = tmp_path / ".jira_nano"
    cfg.mkdir()
    (cfg / "users.yaml").write_text("korkin25:\n  name: Kirill\n  telegram: '@k'\n")
    return build_server(TicketService(tmp_path))


def _tools(server: Any) -> list[Any]:
    return asyncio.run(server.list_tools())


def _call(server: Any, name: str, args: dict[str, Any]) -> Any:
    out = asyncio.run(server.call_tool(name, args))
    contents = out[0] if isinstance(out, tuple) else out
    return json.loads(contents[0].text)


def test_expected_tool_set_present(server: Any) -> None:
    assert {t.name for t in _tools(server)} >= EXPECTED_TOOLS


def test_all_tools_use_jira_prefix(server: Any) -> None:
    assert all(t.name.startswith("jira_") for t in _tools(server))


def test_create_issue_arg_names_match(server: Any) -> None:
    create = next(t for t in _tools(server) if t.name == "jira_create_issue")
    props = set(create.inputSchema["properties"])
    assert {"summary", "reporter", "issuetype", "description", "priority", "assignee"} <= props


def test_delete_archives(server: Any) -> None:
    _call(server, "jira_create_issue", {"summary": "a", "reporter": "e"})
    result = _call(server, "jira_delete_issue", {"issue_key": "JN-1"})
    assert result["fields"]["status"]["name"] == "Archived"


def test_batch_create(server: Any) -> None:
    result = _call(
        server,
        "jira_batch_create_issues",
        {"issues": [{"summary": "a", "reporter": "e"}, {"summary": "b", "reporter": "e"}]},
    )
    assert result["total"] == 2
    assert [i["key"] for i in result["issues"]] == ["JN-1", "JN-2"]


def test_user_profile_and_assignable(server: Any) -> None:
    profile = _call(server, "jira_get_user_profile", {"username": "korkin25"})
    assert profile["displayName"] == "Kirill"
    assignable = _call(server, "jira_search_assignable_users", {"query": "kor"})
    assert [u["name"] for u in assignable["users"]] == ["korkin25"]
