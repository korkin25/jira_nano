"""SKILL.md (Agent Skill) validation — JN-25."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

SKILL = Path(__file__).resolve().parent.parent / "SKILL.md"


def _frontmatter() -> dict[str, Any]:
    text = SKILL.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    assert match is not None, "SKILL.md is missing YAML frontmatter"
    data: dict[str, Any] = yaml.safe_load(match.group(1))
    return data


def test_skill_exists() -> None:
    assert SKILL.is_file()


def test_frontmatter_required_fields() -> None:
    fm = _frontmatter()
    assert fm["name"] == "jira_nano"
    assert isinstance(fm["description"], str) and len(fm["description"]) >= 40


def test_body_mentions_mcp_tools() -> None:
    body = SKILL.read_text(encoding="utf-8")
    assert "jira_create_issue" in body
    assert "jira_transition_issue" in body
