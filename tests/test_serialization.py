"""Round-trip (de)serialization tests for tickets/JN-<n>.md — JN-1 (TDD).

Example of the first failing test to write in the dev chat: parsing then
serializing a canonical ticket must be byte-stable.
"""
from __future__ import annotations

import pytest


@pytest.mark.skip(reason="TDD: write test-first in the Phase 1 dev chat (JN-1)")
def test_roundtrip_is_stable() -> None:
    from jira_nano.serialization import dumps, loads

    text = "---\n...canonical ticket fixture...\n---\n\n## Description\n\n...\n"
    assert dumps(loads(text)) == text
