"""Rich read views — single-ticket card + board listing."""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from jira_nano.config import DEFAULT_WORKFLOW
from jira_nano.models import Link, LinkType, Ticket
from jira_nano.telegram.views import render_board, render_ticket
from jira_nano.users import UserDirectory

_T0 = datetime(2026, 7, 24, 9, 0, 0, tzinfo=UTC)


def _t(**over: Any) -> Ticket:
    data: dict[str, Any] = {
        "id": "JN-42", "title": "Fix login", "reporter": "e", "created": _T0, "updated": _T0,
    }
    data.update(over)
    return Ticket(**data)


def test_render_ticket_card() -> None:
    t = _t(status="in-review", assignee="korkin25", priority="high",
           links=[Link(type=LinkType.mr, url="https://x/128", ref="!128")])
    out = render_ticket(DEFAULT_WORKFLOW, t)
    assert out.startswith("🟣 <b>Fix login</b>\n<blockquote>")
    assert "<b>id</b> · <code>JN-42</code>" in out
    assert "<b>status</b> · 🟣 in-review" in out
    assert "<b>assignee</b> · @korkin25" in out          # no directory -> fallback
    assert "<b>priority</b> · 🔺 high" in out
    assert '<b>mr</b> · <a href="https://x/128">!128</a>' in out
    assert out.endswith("</blockquote>")


def test_render_ticket_unassigned_and_blocked() -> None:
    out = render_ticket(DEFAULT_WORKFLOW, _t(blocked=True, blocked_reason="waiting"))
    assert "<b>blocked</b> · 🚫" in out
    assert "<b>assignee</b> · <i>unassigned</i>" in out


def test_render_ticket_escapes_html() -> None:
    assert "a &lt;b&gt; &amp; c" in render_ticket(DEFAULT_WORKFLOW, _t(title="a <b> & c"))


def test_render_board() -> None:
    tickets = [
        _t(id="JN-40", title="Auth refactor", status="done", assignee="lesya"),
        _t(id="JN-42", title="Fix login", status="in-review"),
    ]
    out = render_board(DEFAULT_WORKFLOW, tickets, title="Sprint 12")
    assert out.startswith("🗂 <b>Sprint 12</b>\n<blockquote>")
    assert "1. 🟢 <b><code>JN-40</code></b> — Auth refactor · @lesya" in out
    assert "2. 🟣 <b><code>JN-42</code></b> — Fix login · <i>unassigned</i>" in out
    assert out.endswith("</blockquote>")


def test_render_board_empty() -> None:
    expected = "🗂 <b>Board</b>\n<blockquote><i>empty</i></blockquote>"
    assert render_board(DEFAULT_WORKFLOW, []) == expected


def test_render_board_uses_directory_mention(tmp_path: Path) -> None:
    cfg = tmp_path / ".jira_nano"
    cfg.mkdir()
    (cfg / "users.yaml").write_text("korkin25:\n  telegram: '@kork'\n")
    directory = UserDirectory.load(cfg)
    out = render_board(DEFAULT_WORKFLOW, [_t(assignee="korkin25")], directory=directory)
    assert "· @kork" in out
