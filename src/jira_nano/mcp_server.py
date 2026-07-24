"""MCP server (FastMCP, stdio) — JN-11 / JN-D6.

Thin adapters over :class:`TicketService`: each tool maps Jira-shaped arguments
onto the service and returns Jira issue JSON (via the mapper, JN-33). Search uses
the JQL subset (JN-30). Jira-exact naming/shape conformance is polished in JN-12.
"""
from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .jira.jql import run as run_jql
from .jira.mapper import to_jira_issue
from .models import Ticket
from .service import TicketService
from .users import UserDirectory


def build_server(service: TicketService, version: int = 2) -> FastMCP:
    """Build a FastMCP server exposing the jira_nano tool surface over ``service``."""
    server = FastMCP("jira_nano")
    directory = UserDirectory.load(service.paths.config_dir)

    def issue(ticket: Ticket) -> dict[str, Any]:
        return to_jira_issue(ticket, version, directory)

    @server.tool()
    def jira_create_issue(
        summary: str,
        reporter: str,
        issuetype: str = "Task",
        description: str = "",
        priority: str = "Medium",
        assignee: str | None = None,
        labels: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new issue."""
        return issue(
            service.create(
                title=summary,
                reporter=reporter,
                type=issuetype.lower(),
                description=description,
                priority=priority.lower(),
                assignee=assignee,
                labels=labels or [],
            )
        )

    @server.tool()
    def jira_get_issue(issue_key: str) -> dict[str, Any]:
        """Get an issue by key."""
        return issue(service.get(issue_key))

    @server.tool()
    def jira_update_issue(
        issue_key: str,
        summary: str | None = None,
        description: str | None = None,
        priority: str | None = None,
        labels: list[str] | None = None,
    ) -> dict[str, Any]:
        """Update issue fields."""
        changes: dict[str, Any] = {}
        if summary is not None:
            changes["title"] = summary
        if description is not None:
            changes["description"] = description
        if priority is not None:
            changes["priority"] = priority.lower()
        if labels is not None:
            changes["labels"] = labels
        return issue(service.update(issue_key, **changes))

    @server.tool()
    def jira_search(jql: str) -> dict[str, Any]:
        """Search issues with a JQL query (Jira-shaped response envelope)."""
        issues = [issue(t) for t in run_jql(service.conn, jql)]
        return {"issues": issues, "total": len(issues)}

    @server.tool()
    def jira_get_transitions(issue_key: str) -> dict[str, Any]:
        """List the legal transitions for an issue."""
        return {"transitions": [{"name": s} for s in service.get_transitions(issue_key)]}

    @server.tool()
    def jira_transition_issue(issue_key: str, status: str) -> dict[str, Any]:
        """Transition an issue to a new status (validated against the workflow)."""
        return issue(service.transition(issue_key, status))

    @server.tool()
    def jira_assign_issue(issue_key: str, assignee: str | None) -> dict[str, Any]:
        """Assign an issue to a user (or unassign with null)."""
        return issue(service.assign(issue_key, assignee))

    @server.tool()
    def jira_add_comment(issue_key: str, body: str, author: str) -> dict[str, Any]:
        """Add a comment to an issue."""
        return issue(service.comment(issue_key, author=author, body=body))

    @server.tool()
    def jira_add_watcher(issue_key: str, watcher: str) -> dict[str, Any]:
        """Add a watcher to an issue."""
        return issue(service.add_watcher(issue_key, watcher))

    @server.tool()
    def jira_remove_watcher(issue_key: str, watcher: str) -> dict[str, Any]:
        """Remove a watcher from an issue."""
        return issue(service.remove_watcher(issue_key, watcher))

    @server.tool()
    def jira_get_issue_watchers(issue_key: str) -> dict[str, Any]:
        """Get the watchers of an issue."""
        return {"watchers": service.get_watchers(issue_key)}

    @server.tool()
    def jira_link_to_epic(issue_key: str, epic_key: str) -> dict[str, Any]:
        """Link an issue to a parent epic."""
        return issue(service.link_epic(issue_key, epic_key))

    @server.tool()
    def jira_delete_issue(issue_key: str) -> dict[str, Any]:
        """Archive an issue (no hard delete — JN-D6)."""
        return issue(service.update(issue_key, status="archived"))

    @server.tool()
    def jira_batch_create_issues(issues: list[dict[str, Any]]) -> dict[str, Any]:
        """Create several issues at once."""
        created = [
            issue(
                service.create(
                    title=spec["summary"],
                    reporter=spec["reporter"],
                    type=spec.get("issuetype", "Task").lower(),
                    description=spec.get("description", ""),
                    priority=spec.get("priority", "Medium").lower(),
                    assignee=spec.get("assignee"),
                    labels=spec.get("labels", []),
                )
            )
            for spec in issues
        ]
        return {"issues": created, "total": len(created)}

    @server.tool()
    def jira_get_project_issues() -> dict[str, Any]:
        """List every issue in the project."""
        issues = [issue(t) for t in service.list_tickets()]
        return {"issues": issues, "total": len(issues)}

    @server.tool()
    def jira_edit_comment(issue_key: str, comment_id: int, body: str) -> dict[str, Any]:
        """Edit an existing comment."""
        return issue(service.edit_comment(issue_key, comment_id, body))

    @server.tool()
    def jira_create_remote_issue_link(
        issue_key: str,
        url: str,
        link_type: str = "issue",
        host: str | None = None,
        ref: str | None = None,
    ) -> dict[str, Any]:
        """Add a remote/web link (commit / MR / PR / URL) to an issue."""
        return issue(service.add_link(issue_key, type=link_type, url=url, host=host, ref=ref))

    @server.tool()
    def jira_get_user_profile(username: str) -> dict[str, Any]:
        """Get a user's profile from the directory."""
        user = directory.resolve(username)
        return {
            "accountId": user.account_id or user.handle,
            "name": user.handle,
            "displayName": user.name or user.handle,
            "emailAddress": user.email,
        }

    @server.tool()
    def jira_search_assignable_users(query: str = "") -> dict[str, Any]:
        """List users assignable to issues (from the directory)."""
        needle = query.lower()
        users = [
            {
                "accountId": u.account_id or u.handle,
                "name": u.handle,
                "displayName": u.name or u.handle,
            }
            for u in directory.all_users()
            if needle in u.handle.lower() or (u.name is not None and needle in u.name.lower())
        ]
        return {"users": users}

    return server
