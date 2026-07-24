"""JQL subset parser + executor (JN-30 / JN-D5).

Supported grammar (a pragmatic subset of JQL):

    expr    := or_expr
    or_expr := and_expr (OR and_expr)*
    and_expr:= cond (AND cond)*
    cond    := field OP value | field IN ( value, ... )
    OP      := '=' | '!=' | '~'
    tail    := [ ORDER BY field [ASC|DESC] ]

Fields: ``status``, ``assignee``, ``reporter``, ``priority``, ``type``
(``issuetype``), ``parent``, ``labels``, ``text`` (full-text). Results are
reconstructed from the cache's ``ticket_json`` column.
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from typing import Any

from jira_nano.errors import JqlError
from jira_nano.models import Ticket

_FIELD_COLUMNS = {
    "status": "status",
    "assignee": "assignee",
    "reporter": "reporter",
    "priority": "priority",
    "type": "type",
    "issuetype": "type",
    "parent": "parent",
}
_ORDER_COLUMNS = {
    **_FIELD_COLUMNS,
    "key": "id",
    "id": "id",
    "created": "created",
    "updated": "updated",
}
_KEYWORDS = {"and", "or", "in", "order", "by", "asc", "desc"}

_TOKEN_RE = re.compile(
    r"""\s+
      | (?P<str>'[^']*'|\"[^\"]*\")
      | (?P<op>!=|=|~)
      | (?P<lparen>\()
      | (?P<rparen>\))
      | (?P<comma>,)
      | (?P<word>[A-Za-z0-9_\-.@:/]+)
    """,
    re.VERBOSE,
)


@dataclass
class Cond:
    field: str
    op: str
    values: list[str]


@dataclass
class BoolNode:
    op: str  # "AND" | "OR"
    children: list[Any]


def _tokenize(jql: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    pos = 0
    while pos < len(jql):
        match = _TOKEN_RE.match(jql, pos)
        if match is None or match.end() == pos:
            raise JqlError(f"unexpected character at {pos}: {jql[pos:pos + 10]!r}")
        pos = match.end()
        kind = match.lastgroup
        if kind is None:  # whitespace
            continue
        value = match.group()
        if kind == "str":
            tokens.append(("str", value[1:-1]))
        elif kind == "word" and value.lower() in _KEYWORDS:
            tokens.append(("kw", value.lower()))
        else:
            tokens.append((kind, value))
    return tokens


class _Parser:
    def __init__(self, tokens: list[tuple[str, str]]) -> None:
        self.tokens = tokens
        self.pos = 0

    def _peek(self) -> tuple[str, str] | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def _next(self) -> tuple[str, str]:
        if self.pos >= len(self.tokens):
            raise JqlError("unexpected end of query")
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def parse(self) -> tuple[Any | None, tuple[str, str] | None]:
        where = None if self._is_order() else self._or()
        order = self._order()
        if self._peek() is not None:
            raise JqlError(f"unexpected token: {self._peek()}")
        return where, order

    def _is_order(self) -> bool:
        token = self._peek()
        return token == ("kw", "order")

    def _or(self) -> Any:
        nodes = [self._and()]
        while self._peek() == ("kw", "or"):
            self._next()
            nodes.append(self._and())
        return nodes[0] if len(nodes) == 1 else BoolNode("OR", nodes)

    def _and(self) -> Any:
        nodes = [self._cond()]
        while self._peek() == ("kw", "and"):
            self._next()
            nodes.append(self._cond())
        return nodes[0] if len(nodes) == 1 else BoolNode("AND", nodes)

    def _cond(self) -> Cond:
        field_kind, field = self._next()
        if field_kind != "word":
            raise JqlError(f"expected a field name, got {field!r}")
        op_token = self._next()
        if op_token == ("kw", "in"):
            return Cond(field.lower(), "in", self._value_list())
        if op_token[0] != "op":
            raise JqlError(f"expected an operator after {field!r}, got {op_token[1]!r}")
        return Cond(field.lower(), op_token[1], [self._value()])

    def _value(self) -> str:
        kind, value = self._next()
        if kind not in ("str", "word"):
            raise JqlError(f"expected a value, got {value!r}")
        return value

    def _value_list(self) -> list[str]:
        if self._next()[0] != "lparen":
            raise JqlError("expected '(' after IN")
        values = [self._value()]
        token = self._peek()
        while token is not None and token[0] == "comma":
            self._next()
            values.append(self._value())
            token = self._peek()
        if self._next()[0] != "rparen":
            raise JqlError("expected ')' to close IN list")
        return values

    def _order(self) -> tuple[str, str] | None:
        if self._peek() != ("kw", "order"):
            return None
        self._next()
        if self._next() != ("kw", "by"):
            raise JqlError("expected BY after ORDER")
        field = self._value().lower()
        direction = "ASC"
        if self._peek() in (("kw", "asc"), ("kw", "desc")):
            direction = self._next()[1].upper()
        return field, direction


def _cond_sql(cond: Cond) -> tuple[str, list[str]]:
    field = cond.field
    if field == "text":
        return "t.id IN (SELECT ticket_id FROM tickets_fts WHERE tickets_fts MATCH ?)", cond.values
    if field == "labels":
        placeholders = ",".join("?" * len(cond.values))
        clause = f"SELECT 1 FROM ticket_labels WHERE ticket_id = t.id AND label IN ({placeholders})"
        negate = "NOT " if cond.op == "!=" else ""
        return f"{negate}EXISTS ({clause})", list(cond.values)
    column = _FIELD_COLUMNS.get(field)
    if column is None:
        raise JqlError(f"unsupported field: {field!r}")
    if cond.op == "=":
        return f"t.{column} = ?", cond.values
    if cond.op == "!=":
        return f"t.{column} != ?", cond.values
    if cond.op == "~":
        return f"t.{column} LIKE ?", [f"%{cond.values[0]}%"]
    if cond.op == "in":
        placeholders = ",".join("?" * len(cond.values))
        return f"t.{column} IN ({placeholders})", list(cond.values)
    raise JqlError(f"unsupported operator: {cond.op!r}")


def _compile(node: Any) -> tuple[str, list[str]]:
    if isinstance(node, Cond):
        return _cond_sql(node)
    parts: list[str] = []
    params: list[str] = []
    for child in node.children:
        sql, child_params = _compile(child)
        parts.append(sql)
        params.extend(child_params)
    joiner = f" {node.op} "
    return "(" + joiner.join(parts) + ")", params


def to_sql(jql: str) -> tuple[str, list[str]]:
    """Translate a JQL string into an SQL query over the cache's ``tickets`` table."""
    where, order = _Parser(_tokenize(jql)).parse()
    sql = "SELECT t.ticket_json FROM tickets t"
    params: list[str] = []
    if where is not None:
        clause, params = _compile(where)
        sql += f" WHERE {clause}"
    if order is not None:
        field, direction = order
        column = _ORDER_COLUMNS.get(field)
        if column is None:
            raise JqlError(f"cannot order by {field!r}")
        sql += f" ORDER BY t.{column} {direction}"
    else:
        sql += " ORDER BY t.created, t.id"
    return sql, params


def run(conn: sqlite3.Connection, jql: str) -> list[Ticket]:
    """Execute a JQL query against the cache and return the matching tickets."""
    sql, params = to_sql(jql)
    return [Ticket.model_validate_json(row[0]) for row in conn.execute(sql, params).fetchall()]
