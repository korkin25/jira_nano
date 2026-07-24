"""HTTP API — Jira REST v2 + v3 — JN-13."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pygit2
import pytest
from fastapi.testclient import TestClient

from jira_nano.http.app import build_app
from jira_nano.http.auth import Authenticator, Credentials
from jira_nano.service import TicketService

H = {"Authorization": "Bearer tok"}


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    pygit2.init_repository(str(tmp_path), bare=False)
    service = TicketService(tmp_path)
    auth = Authenticator(Credentials(tokens={"tok": "eugeny"}, oauth_clients={"cli": "sec"}))
    return TestClient(build_app(service, auth))


def _create(client: TestClient, fields: dict[str, Any], version: str = "2") -> str:
    r = client.post(f"/rest/api/{version}/issue", json={"fields": fields}, headers=H)
    assert r.status_code == 201, r.text
    return str(r.json()["key"])


def test_requires_auth(client: TestClient) -> None:
    r = client.get("/rest/api/2/issue/JN-1")
    assert r.status_code == 401
    assert "errorMessages" in r.json()


def test_create_and_get_v2(client: TestClient) -> None:
    key = _create(client, {"summary": "Hi", "description": "steps"})
    assert key == "JN-1"
    got = client.get(f"/rest/api/2/issue/{key}", headers=H).json()
    assert got["fields"]["summary"] == "Hi"
    assert got["fields"]["description"] == "steps"  # v2 plain string


def test_v3_adf_and_latest_alias(client: TestClient) -> None:
    _create(client, {"summary": "Hi", "description": "body"})
    got = client.get("/rest/api/latest/issue/JN-1", headers=H).json()
    assert got["fields"]["description"]["type"] == "doc"  # v3 ADF via 'latest'


def test_update_and_delete(client: TestClient) -> None:
    _create(client, {"summary": "x"})
    r = client.put("/rest/api/2/issue/JN-1", json={"fields": {"summary": "y"}}, headers=H)
    assert r.status_code == 204
    assert client.get("/rest/api/2/issue/JN-1", headers=H).json()["fields"]["summary"] == "y"
    r = client.delete("/rest/api/2/issue/JN-1", headers=H)
    assert r.status_code == 204
    status = client.get("/rest/api/2/issue/JN-1", headers=H).json()["fields"]["status"]
    assert status["name"] == "Archived"


def test_transition_flow(client: TestClient) -> None:
    _create(client, {"summary": "x"})
    illegal = client.post(
        "/rest/api/2/issue/JN-1/transitions", json={"transition": {"id": "done"}}, headers=H
    )
    assert illegal.status_code == 400
    client.put("/rest/api/2/issue/JN-1/assignee", json={"name": "korkin25"}, headers=H)
    legal = client.post(
        "/rest/api/2/issue/JN-1/transitions", json={"transition": {"id": "in-progress"}}, headers=H
    )
    assert legal.status_code == 204


def test_comment(client: TestClient) -> None:
    _create(client, {"summary": "x"})
    r = client.post("/rest/api/2/issue/JN-1/comment", json={"body": "hello"}, headers=H)
    assert r.status_code == 201
    assert r.json()["body"] == "hello"


def test_search_v2_envelope(client: TestClient) -> None:
    _create(client, {"summary": "alpha"})
    body = client.get("/rest/api/2/search", params={"jql": "text ~ alpha"}, headers=H).json()
    assert body["total"] == 1 and "startAt" in body
    assert [i["key"] for i in body["issues"]] == ["JN-1"]


def test_search_v3_envelope(client: TestClient) -> None:
    _create(client, {"summary": "alpha"})
    body = client.post("/rest/api/3/search/jql", json={"jql": "text ~ alpha"}, headers=H).json()
    assert "nextPageToken" in body and body["isLast"] is True
    assert [i["key"] for i in body["issues"]] == ["JN-1"]


def test_not_found(client: TestClient) -> None:
    assert client.get("/rest/api/2/issue/JN-99", headers=H).status_code == 404


def test_oauth_token_then_bearer(client: TestClient) -> None:
    grant = client.post(
        "/oauth/token",
        json={"grant_type": "client_credentials", "client_id": "cli", "client_secret": "sec"},
    )
    assert grant.status_code == 200
    token = grant.json()["access_token"]
    # auth passes (404 for missing issue, not 401)
    r = client.get("/rest/api/2/issue/JN-1", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 404
