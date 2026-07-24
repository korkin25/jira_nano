"""Command-line interface over the service layer (JN-38).

A thin CLI for humans and scripts: ``jira-nano <command>``. It calls the same
:class:`TicketService` as the MCP and HTTP surfaces. The repo is taken from
``--repo``, ``$JIRA_NANO_REPO``, or the current directory.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .errors import JiraNanoError
from .jira.jql import run as run_jql
from .service import TicketService

REPO_ENV = "JIRA_NANO_REPO"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jira-nano", description="jira_nano ticket CLI")
    parser.add_argument("--repo", default=os.environ.get(REPO_ENV, "."))
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="create a ticket")
    create.add_argument("--title", required=True)
    create.add_argument("--reporter", required=True)
    create.add_argument("--type", default="task")
    create.add_argument("--priority", default="medium")

    sub.add_parser("get", help="show a ticket").add_argument("key")
    sub.add_parser("list", help="list tickets").add_argument("--status")
    sub.add_parser("search", help="search with JQL").add_argument("jql")

    transition = sub.add_parser("transition", help="move a ticket's status")
    transition.add_argument("key")
    transition.add_argument("status")

    assign = sub.add_parser("assign", help="assign a ticket")
    assign.add_argument("key")
    assign.add_argument("assignee")

    comment = sub.add_parser("comment", help="add a comment")
    comment.add_argument("key")
    comment.add_argument("--author", required=True)
    comment.add_argument("--body", required=True)

    sub.add_parser("board", help="show the board grouped by status")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    service = TicketService(Path(args.repo))
    try:
        if args.command == "create":
            ticket = service.create(
                title=args.title, reporter=args.reporter, type=args.type, priority=args.priority
            )
            print(ticket.id)
        elif args.command == "get":
            print(service.get(args.key).model_dump_json(indent=2))
        elif args.command == "list":
            filters = {"status": args.status} if args.status else {}
            for ticket in service.list_tickets(**filters):
                print(f"{ticket.id}\t{ticket.status.value}\t{ticket.title}")
        elif args.command == "search":
            for ticket in run_jql(service.conn, args.jql):
                print(f"{ticket.id}\t{ticket.status.value}\t{ticket.title}")
        elif args.command == "transition":
            print(service.transition(args.key, args.status).status.value)
        elif args.command == "assign":
            service.assign(args.key, args.assignee)
            print(args.key)
        elif args.command == "comment":
            service.comment(args.key, author=args.author, body=args.body)
            print(args.key)
        elif args.command == "board":
            for status, tickets in service.board().items():
                print(status.value)
                for ticket in tickets:
                    print(f"  {ticket.id}\t{ticket.title}")
    except JiraNanoError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0
