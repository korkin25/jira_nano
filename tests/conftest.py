"""Shared pytest fixtures.

Filled in test-first during the Phase 1 dev chat (TDD). The core fixture is a
temporary jira_nano repository (git init + ``tickets/`` + ``.jira_nano/``).
"""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A temporary jira_nano repository.

    TODO(JN-2/JN-28): initialize a pygit2 repo with sample tickets and a default
    ``.jira_nano/`` (workflow.yaml + users.yaml), and return its root.
    """
    return tmp_path
