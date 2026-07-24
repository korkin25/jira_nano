"""Packaging / distribution metadata — JN-27."""
from __future__ import annotations

from importlib.metadata import entry_points, version

import jira_nano


def test_distribution_is_installed() -> None:
    assert version("jira-nano")  # importlib.metadata can resolve the distribution


def test_package_exposes_version() -> None:
    assert isinstance(jira_nano.__version__, str) and jira_nano.__version__


def test_console_scripts_declared() -> None:
    names = {ep.name for ep in entry_points(group="console_scripts")}
    assert {"jira-nano", "jira-nano-mcp"} <= names
