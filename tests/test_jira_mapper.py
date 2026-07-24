"""Ticket <-> Jira issue JSON mapping — JN-33."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from jira_nano.jira.mapper import FLAGGED_FIELD, fields_from_jira, to_jira_issue
from jira_nano.models import Ticket

_T0 = datetime(2026, 7, 24, 9, 0, 0, tzinfo=UTC)


def _ticket(**over: Any) -> Ticket:
    data: dict[str, Any] = {
        "id": "JN-123",
        "title": "Fix login",
        "reporter": "eugeny",
        "created": _T0,
        "updated": _T0,
    }
    data.update(over)
    return Ticket(**data)


def test_v2_basic_fields() -> None:
    issue = to_jira_issue(_ticket(assignee="korkin25", description="steps"), version=2)
    assert issue["key"] == "JN-123"
    assert issue["id"] == "123"
    fields = issue["fields"]
    assert fields["summary"] == "Fix login"
    assert fields["description"] == "steps"  # plain string in v2
    assert fields["issuetype"] == {"name": "Task"}
    assert fields["assignee"]["name"] == "korkin25"  # username in v2
    assert fields["priority"]["name"] == "Medium"


def test_status_category() -> None:
    review = to_jira_issue(_ticket(status="in-review", assignee="k"))["fields"]["status"]
    assert review["statusCategory"]["key"] == "indeterminate"
    archived = to_jira_issue(_ticket(status="archived"))["fields"]["status"]
    assert archived["statusCategory"]["key"] == "done"


def test_v3_adf_and_account_id() -> None:
    fields = to_jira_issue(_ticket(assignee="korkin25", description="hi"), version=3)["fields"]
    assert fields["assignee"]["accountId"] == "korkin25"
    assert fields["description"]["type"] == "doc"
    text = fields["description"]["content"][0]["content"][0]["text"]
    assert text == "hi"


def test_blocked_sets_flagged() -> None:
    fields = to_jira_issue(_ticket(blocked=True, blocked_reason="x"))["fields"]
    assert fields[FLAGGED_FIELD] == [{"value": "Impediment"}]


def test_resolution_and_parent() -> None:
    ticket = _ticket(status="archived", resolution="wontfix", parent="JN-100")
    fields = to_jira_issue(ticket)["fields"]
    assert fields["resolution"] == {"name": "Won't Do"}
    assert fields["parent"] == {"key": "JN-100"}


def test_fields_from_jira_roundtrip() -> None:
    original = _ticket(
        assignee="korkin25", description="body", type="bug", priority="high", labels=["backend"]
    )
    recovered = fields_from_jira(to_jira_issue(original, version=2)["fields"])
    assert recovered["title"] == "Fix login"
    assert recovered["description"] == "body"
    assert recovered["type"] == "bug"
    assert recovered["priority"] == "high"
    assert recovered["assignee"] == "korkin25"
    assert recovered["labels"] == ["backend"]


def test_comments_mapped() -> None:
    from jira_nano.models import Comment

    ticket = _ticket(
        comments=[Comment(id=1, author="korkin25", source="telegram", at=_T0, body="hello")]
    )
    comments = to_jira_issue(ticket)["fields"]["comment"]["comments"]
    assert comments[0]["id"] == "1"
    assert comments[0]["body"] == "hello"
