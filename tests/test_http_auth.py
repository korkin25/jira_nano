"""HTTP authentication — Basic / Bearer PAT / OAuth 2.0 — JN-32."""
from __future__ import annotations

import base64

import pytest

from jira_nano.errors import AuthError
from jira_nano.http.auth import Authenticator, Credentials


def _basic(username: str, token: str) -> str:
    raw = base64.b64encode(f"{username}:{token}".encode()).decode()
    return f"Basic {raw}"


def _auth() -> Authenticator:
    return Authenticator(
        Credentials(tokens={"pat-123": "korkin25"}, oauth_clients={"cli": "s3cret"})
    )


def test_basic_valid() -> None:
    assert _auth().authenticate(_basic("korkin25", "pat-123")) == "korkin25"


def test_basic_wrong_token() -> None:
    with pytest.raises(AuthError):
        _auth().authenticate(_basic("korkin25", "nope"))


def test_bearer_pat_valid() -> None:
    assert _auth().authenticate("Bearer pat-123") == "korkin25"


def test_bearer_invalid() -> None:
    with pytest.raises(AuthError):
        _auth().authenticate("Bearer nope")


def test_missing_header() -> None:
    with pytest.raises(AuthError):
        _auth().authenticate(None)


def test_unsupported_scheme() -> None:
    with pytest.raises(AuthError):
        _auth().authenticate("Digest abc")


def test_oauth_client_credentials_flow() -> None:
    auth = _auth()
    grant = auth.issue_token("cli", "s3cret")
    assert grant["token_type"] == "Bearer"
    token = str(grant["access_token"])
    assert auth.authenticate(f"Bearer {token}") == "cli"


def test_oauth_invalid_client() -> None:
    with pytest.raises(AuthError):
        _auth().issue_token("cli", "wrong")


def test_credentials_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JIRA_NANO_TOKENS", "korkin25:pat-abc, bob:pat-xyz")
    monkeypatch.setenv("JIRA_NANO_OAUTH_CLIENTS", "cli:secret")
    creds = Credentials.from_env()
    assert creds.tokens == {"pat-abc": "korkin25", "pat-xyz": "bob"}
    assert creds.oauth_clients == {"cli": "secret"}
