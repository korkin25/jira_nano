"""Remote MCP over streamable-HTTP transport — JN-34."""
from __future__ import annotations

from pathlib import Path

import pygit2
import pytest
from starlette.applications import Starlette

from jira_nano.mcp_server import http_app
from jira_nano.service import TicketService


@pytest.fixture
def service(tmp_path: Path) -> TicketService:
    pygit2.init_repository(str(tmp_path), bare=False)
    return TicketService(tmp_path)


def test_http_app_is_asgi(service: TicketService) -> None:
    app = http_app(service)
    assert isinstance(app, Starlette)
    assert callable(app)  # ASGI-callable
