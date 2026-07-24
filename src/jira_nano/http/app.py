"""HTTP API — Jira REST v2 + v3 (JN-13 / JN-D5).

A FastAPI app serving ``/rest/api/{2,3,latest}/...`` as a drop-in Jira REST
surface: endpoints map onto the service layer, bodies use the mapper (v2 strings
/ v3 ADF), search uses the JQL subset, and auth uses :mod:`jira_nano.http.auth`.
Errors use Jira's ``{"errorMessages": [...], "errors": {...}}`` envelope.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import Body, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError as PydanticValidationError

from jira_nano.errors import AuthError, JqlError, TicketNotFoundError, TransitionError
from jira_nano.jira.jql import run as run_jql
from jira_nano.jira.mapper import fields_from_jira, to_jira_issue
from jira_nano.service import TicketService
from jira_nano.users import UserDirectory

from .auth import Authenticator, Credentials


def _envelope(messages: list[str], status: int) -> JSONResponse:
    return JSONResponse({"errorMessages": messages, "errors": {}}, status_code=status)


def build_app(service: TicketService, authenticator: Authenticator | None = None) -> FastAPI:
    """Build the FastAPI app backed by ``service``."""
    app = FastAPI(title="jira_nano")
    directory = UserDirectory.load(service.paths.config_dir)
    auth = authenticator if authenticator is not None else Authenticator(Credentials.from_env())

    def require(authorization: str | None) -> str:
        return auth.authenticate(authorization)

    def version_of(version: str) -> int:
        if version in ("3", "latest"):
            return 3
        if version == "2":
            return 2
        raise HTTPException(status_code=404, detail="unknown API version")

    @app.exception_handler(AuthError)
    async def _on_auth(request: Request, exc: AuthError) -> JSONResponse:
        return _envelope([str(exc)], 401)

    @app.exception_handler(TicketNotFoundError)
    async def _on_missing(request: Request, exc: TicketNotFoundError) -> JSONResponse:
        return _envelope([f"Issue does not exist: {exc}"], 404)

    @app.exception_handler(TransitionError)
    async def _on_transition(request: Request, exc: TransitionError) -> JSONResponse:
        return _envelope([str(exc)], 400)

    @app.exception_handler(JqlError)
    async def _on_jql(request: Request, exc: JqlError) -> JSONResponse:
        return _envelope([str(exc)], 400)

    @app.exception_handler(PydanticValidationError)
    async def _on_validation(request: Request, exc: PydanticValidationError) -> JSONResponse:
        return _envelope([str(exc)], 400)

    @app.post("/oauth/token")
    def oauth_token(body: dict[str, Any] = Body(default={})) -> dict[str, Any]:
        return auth.issue_token(body.get("client_id", ""), body.get("client_secret", ""))

    @app.get("/rest/api/{version}/myself")
    def myself(version: str, authorization: str | None = Header(default=None)) -> dict[str, Any]:
        who = require(authorization)
        version_of(version)
        return {"name": who, "accountId": who, "displayName": who}

    @app.get("/rest/api/{version}/issue/{key}")
    def get_issue(
        version: str, key: str, authorization: str | None = Header(default=None)
    ) -> dict[str, Any]:
        require(authorization)
        return to_jira_issue(service.get(key), version_of(version), directory)

    @app.post("/rest/api/{version}/issue", status_code=201)
    def create_issue(
        version: str,
        body: dict[str, Any] = Body(...),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        who = require(authorization)
        v = version_of(version)
        fields = fields_from_jira(body.get("fields", {}))
        title = fields.pop("title", "")
        return to_jira_issue(service.create(title=title, reporter=who, **fields), v, directory)

    @app.put("/rest/api/{version}/issue/{key}", status_code=204)
    def update_issue(
        version: str,
        key: str,
        body: dict[str, Any] = Body(...),
        authorization: str | None = Header(default=None),
    ) -> Response:
        require(authorization)
        version_of(version)
        service.update(key, **fields_from_jira(body.get("fields", {})))
        return Response(status_code=204)

    @app.delete("/rest/api/{version}/issue/{key}", status_code=204)
    def delete_issue(
        version: str, key: str, authorization: str | None = Header(default=None)
    ) -> Response:
        require(authorization)
        version_of(version)
        service.update(key, status="archived")  # no hard delete (JN-D6)
        return Response(status_code=204)

    @app.get("/rest/api/{version}/issue/{key}/transitions")
    def get_transitions(
        version: str, key: str, authorization: str | None = Header(default=None)
    ) -> dict[str, Any]:
        require(authorization)
        version_of(version)
        targets = service.get_transitions(key)
        return {"transitions": [{"id": s, "name": s, "to": {"name": s}} for s in targets]}

    @app.post("/rest/api/{version}/issue/{key}/transitions", status_code=204)
    def do_transition(
        version: str,
        key: str,
        body: dict[str, Any] = Body(...),
        authorization: str | None = Header(default=None),
    ) -> Response:
        require(authorization)
        version_of(version)
        transition = body.get("transition", {})
        service.transition(key, transition.get("id") or transition.get("name"))
        return Response(status_code=204)

    @app.put("/rest/api/{version}/issue/{key}/assignee", status_code=204)
    def set_assignee(
        version: str,
        key: str,
        body: dict[str, Any] = Body(...),
        authorization: str | None = Header(default=None),
    ) -> Response:
        require(authorization)
        version_of(version)
        service.assign(key, body.get("name") or body.get("accountId"))
        return Response(status_code=204)

    @app.post("/rest/api/{version}/issue/{key}/comment", status_code=201)
    def add_comment(
        version: str,
        key: str,
        body: dict[str, Any] = Body(...),
        authorization: str | None = Header(default=None),
    ) -> dict[str, Any]:
        who = require(authorization)
        v = version_of(version)
        ticket = service.comment(key, author=who, body=body.get("body", ""))
        comments = to_jira_issue(ticket, v, directory)["fields"]["comment"]["comments"]
        return dict(comments[-1])

    @app.get("/rest/api/2/search")
    def search_v2(
        jql: str = "", authorization: str | None = Header(default=None)
    ) -> dict[str, Any]:
        require(authorization)
        issues = [to_jira_issue(t, 2, directory) for t in run_jql(service.conn, jql)]
        return {"startAt": 0, "maxResults": len(issues), "total": len(issues), "issues": issues}

    @app.post("/rest/api/3/search/jql")
    def search_v3(
        body: dict[str, Any] = Body(...), authorization: str | None = Header(default=None)
    ) -> dict[str, Any]:
        require(authorization)
        tickets = run_jql(service.conn, body.get("jql", ""))
        issues = [to_jira_issue(t, 3, directory) for t in tickets]
        return {"nextPageToken": None, "isLast": True, "issues": issues}

    return app


def run(repo: Path | None = None) -> None:  # pragma: no cover - server event loop
    """Console entry point: serve the HTTP Jira REST API with uvicorn."""
    import uvicorn

    root = Path(repo) if repo is not None else Path(os.environ.get("JIRA_NANO_REPO", "."))
    host = os.environ.get("JIRA_NANO_HTTP_HOST", "127.0.0.1")
    port = int(os.environ.get("JIRA_NANO_HTTP_PORT", "8080"))
    app = build_app(TicketService(root), Authenticator(Credentials.from_env()))
    uvicorn.run(app, host=host, port=port)
