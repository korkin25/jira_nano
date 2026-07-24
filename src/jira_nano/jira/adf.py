"""Markdown <-> ADF (Atlassian Document Format) conversion (JN-31 / JN-D5).

A pragmatic converter covering the common nodes: paragraphs, headings, code
blocks, bullet/ordered lists, and inline marks (strong, em, code, link). Unknown
ADF nodes degrade gracefully to their text content.
"""
from __future__ import annotations

import re
from typing import Any

_INLINE_RE = re.compile(r"\*\*(.+?)\*\*|\*(.+?)\*|`(.+?)`|\[(.+?)\]\((.+?)\)")
_BULLET_RE = re.compile(r"^[-*] ")
_ORDERED_RE = re.compile(r"^\d+\. ")


def _inline_to_adf(text: str) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    pos = 0
    for match in _INLINE_RE.finditer(text):
        if match.start() > pos:
            nodes.append({"type": "text", "text": text[pos : match.start()]})
        strong, em, code, link_text, href = match.groups()
        if strong is not None:
            nodes.append({"type": "text", "text": strong, "marks": [{"type": "strong"}]})
        elif em is not None:
            nodes.append({"type": "text", "text": em, "marks": [{"type": "em"}]})
        elif code is not None:
            nodes.append({"type": "text", "text": code, "marks": [{"type": "code"}]})
        else:
            nodes.append(
                {
                    "type": "text",
                    "text": link_text,
                    "marks": [{"type": "link", "attrs": {"href": href}}],
                }
            )
        pos = match.end()
    if pos < len(text):
        nodes.append({"type": "text", "text": text[pos:]})
    return nodes


def _inline_to_md(nodes: list[dict[str, Any]]) -> str:
    out: list[str] = []
    for node in nodes:
        if node.get("type") != "text":
            out.append(_inline_to_md(node.get("content", [])))
            continue
        text = node.get("text", "")
        marks = {m["type"]: m for m in node.get("marks", [])}
        if "code" in marks:
            text = f"`{text}`"
        if "strong" in marks:
            text = f"**{text}**"
        if "em" in marks:
            text = f"*{text}*"
        if "link" in marks:
            text = f"[{text}]({marks['link']['attrs']['href']})"
        out.append(text)
    return "".join(out)


def _list_item(text: str) -> dict[str, Any]:
    return {
        "type": "listItem",
        "content": [{"type": "paragraph", "content": _inline_to_adf(text.strip())}],
    }


def _is_block_start(line: str) -> bool:
    return bool(
        line.startswith(("```", "#"))
        or _BULLET_RE.match(line)
        or _ORDERED_RE.match(line)
    )


def markdown_to_adf(md: str) -> dict[str, Any]:
    """Convert a Markdown string to an ADF document."""
    lines = md.split("\n")
    content: list[dict[str, Any]] = []
    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        if line.strip() == "":
            i += 1
        elif line.startswith("```"):
            i += 1
            code: list[str] = []
            while i < n and not lines[i].startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            content.append(
                {"type": "codeBlock", "content": [{"type": "text", "text": "\n".join(code)}]}
            )
        elif line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            content.append(
                {
                    "type": "heading",
                    "attrs": {"level": min(level, 6)},
                    "content": _inline_to_adf(line[level:].strip()),
                }
            )
            i += 1
        elif _BULLET_RE.match(line):
            items: list[dict[str, Any]] = []
            while i < n and _BULLET_RE.match(lines[i]):
                items.append(_list_item(lines[i][2:]))
                i += 1
            content.append({"type": "bulletList", "content": items})
        elif _ORDERED_RE.match(line):
            ordered: list[dict[str, Any]] = []
            while i < n and _ORDERED_RE.match(lines[i]):
                ordered.append(_list_item(_ORDERED_RE.sub("", lines[i])))
                i += 1
            content.append({"type": "orderedList", "content": ordered})
        else:
            para = [line]
            i += 1
            while i < n and lines[i].strip() != "" and not _is_block_start(lines[i]):
                para.append(lines[i])
                i += 1
            content.append({"type": "paragraph", "content": _inline_to_adf(" ".join(para))})
    return {"type": "doc", "version": 1, "content": content}


def adf_to_markdown(adf: dict[str, Any]) -> str:
    """Convert an ADF document back to a Markdown string."""
    blocks: list[str] = []
    for node in adf.get("content", []):
        kind = node.get("type")
        if kind == "heading":
            level = node.get("attrs", {}).get("level", 1)
            blocks.append("#" * level + " " + _inline_to_md(node.get("content", [])))
        elif kind == "codeBlock":
            code = "".join(c.get("text", "") for c in node.get("content", []))
            blocks.append(f"```\n{code}\n```")
        elif kind in ("bulletList", "orderedList"):
            prefix = "- " if kind == "bulletList" else "1. "
            lines = [
                prefix + _inline_to_md(p.get("content", []))
                for item in node.get("content", [])
                for p in item.get("content", [])
            ]
            blocks.append("\n".join(lines))
        else:  # paragraph or unknown -> its text
            blocks.append(_inline_to_md(node.get("content", [])))
    return "\n\n".join(blocks)
