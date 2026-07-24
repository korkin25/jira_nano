"""Markdown <-> ADF conversion — JN-31."""
from __future__ import annotations

from typing import Any

import pytest

from jira_nano.jira.adf import adf_to_markdown, markdown_to_adf


def test_paragraph() -> None:
    adf = markdown_to_adf("Hello world")
    assert adf["type"] == "doc"
    assert adf["content"][0]["type"] == "paragraph"
    assert adf_to_markdown(adf) == "Hello world"


def test_heading() -> None:
    adf = markdown_to_adf("## Title")
    assert adf["content"][0]["type"] == "heading"
    assert adf["content"][0]["attrs"]["level"] == 2
    assert adf_to_markdown(adf) == "## Title"


def test_inline_marks_roundtrip() -> None:
    md = "a **bold** and *italic* and `code` word"
    assert adf_to_markdown(markdown_to_adf(md)) == md


def test_link_roundtrip() -> None:
    md = "see [docs](https://example.com)"
    adf = markdown_to_adf(md)
    mark = adf["content"][0]["content"][1]["marks"][0]
    assert mark["type"] == "link"
    assert mark["attrs"]["href"] == "https://example.com"
    assert adf_to_markdown(adf) == md


def test_code_block_roundtrip() -> None:
    md = "```\nx = 1\ny = 2\n```"
    adf = markdown_to_adf(md)
    assert adf["content"][0]["type"] == "codeBlock"
    assert adf_to_markdown(adf) == md


def test_bullet_list() -> None:
    adf = markdown_to_adf("- one\n- two")
    assert adf["content"][0]["type"] == "bulletList"
    assert len(adf["content"][0]["content"]) == 2
    assert adf_to_markdown(adf) == "- one\n- two"


@pytest.mark.parametrize(
    "md",
    ["Plain text.", "# H1", "**strong** start", "a\nb multiline paragraph"],
)
def test_roundtrip_stable(md: str) -> None:
    assert adf_to_markdown(markdown_to_adf(md)) == md.replace("\n", " ")


def test_unknown_node_degrades() -> None:
    weird: dict[str, Any] = {
        "type": "doc",
        "version": 1,
        "content": [{"type": "panel", "content": [{"type": "text", "text": "note"}]}],
    }
    assert adf_to_markdown(weird) == "note"
