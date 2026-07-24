"""Link writer — JN-23."""
from __future__ import annotations

from pathlib import Path

import pygit2
import pytest

from jira_nano.githost.links import link_ticket
from jira_nano.models import LinkType
from jira_nano.service import TicketService

_MR = "https://gitlab.com/acme/proj/-/merge_requests/42"


@pytest.fixture
def service(tmp_path: Path) -> TicketService:
    pygit2.init_repository(str(tmp_path), bare=False)
    return TicketService(tmp_path)


def test_link_ticket_adds(service: TicketService) -> None:
    t = service.create(title="x", reporter="e")
    result = link_ticket(service, t.id, type="mr", host="gitlab", url=_MR, ref="!42")
    assert len(result.links) == 1
    assert result.links[0].type is LinkType.mr
    assert result.links[0].ref == "!42"


def test_link_ticket_idempotent(service: TicketService) -> None:
    t = service.create(title="x", reporter="e")
    link_ticket(service, t.id, type="mr", host="gitlab", url=_MR)
    link_ticket(service, t.id, type="mr", host="gitlab", url=_MR)
    assert len(service.get(t.id).links) == 1


def test_link_ticket_distinct_urls(service: TicketService) -> None:
    t = service.create(title="x", reporter="e")
    link_ticket(service, t.id, type="commit", host="github", url="https://x/commit/a")
    link_ticket(service, t.id, type="commit", host="github", url="https://x/commit/b")
    assert len(service.get(t.id).links) == 2
