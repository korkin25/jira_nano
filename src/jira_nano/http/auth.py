"""HTTP authentication — Basic, Bearer PAT, and OAuth 2.0 (JN-32 / JN-D5).

Three schemes, as promised by ``docs/http-api.md``:

- **Basic**  — ``username:token`` (the token must map to that username).
- **Bearer** — a personal access token (PAT) or an OAuth 2.0 access token.
- **OAuth 2.0** — the ``client_credentials`` grant issues bearer access tokens;
  jira_nano acts as its own token issuer. (The interactive authorization-code
  flow is a later addition.)

Credentials come from the environment (never from Git). This module is transport
agnostic — the FastAPI app (JN-13) calls :meth:`Authenticator.authenticate` with
the ``Authorization`` header and :meth:`Authenticator.issue_token` for the token
endpoint.
"""
from __future__ import annotations

import base64
import binascii
import os
import secrets
from dataclasses import dataclass, field

from jira_nano.errors import AuthError


def _parse_pairs(raw: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        key, sep, value = item.partition(":")
        if sep:
            pairs[key.strip()] = value.strip()
    return pairs


@dataclass
class Credentials:
    """Configured static credentials."""

    #: token -> principal (username). Used for Basic and Bearer PAT.
    tokens: dict[str, str] = field(default_factory=dict)
    #: OAuth 2.0 client_id -> client_secret (client_credentials grant).
    oauth_clients: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(cls) -> Credentials:
        """Load credentials from ``JIRA_NANO_TOKENS`` / ``JIRA_NANO_OAUTH_CLIENTS``.

        Both are comma-separated ``name:value`` lists — tokens as ``token:user``
        and OAuth clients as ``client_id:client_secret``.
        """
        tokens = {v: k for k, v in _parse_pairs(os.environ.get("JIRA_NANO_TOKENS", "")).items()}
        clients = _parse_pairs(os.environ.get("JIRA_NANO_OAUTH_CLIENTS", ""))
        return cls(tokens=tokens, oauth_clients=clients)


class Authenticator:
    def __init__(self, credentials: Credentials) -> None:
        self.credentials = credentials
        self._issued: dict[str, str] = {}  # access_token -> principal (client_id)

    def issue_token(self, client_id: str, client_secret: str) -> dict[str, object]:
        """OAuth 2.0 ``client_credentials`` grant: issue a bearer access token."""
        if self.credentials.oauth_clients.get(client_id) != client_secret:
            raise AuthError("invalid_client")
        token = secrets.token_urlsafe(32)
        self._issued[token] = client_id
        return {"access_token": token, "token_type": "Bearer", "expires_in": 3600}

    def authenticate(self, authorization: str | None) -> str:
        """Validate an ``Authorization`` header value; return the principal."""
        if not authorization:
            raise AuthError("missing Authorization header")
        scheme, _, credentials = authorization.partition(" ")
        scheme = scheme.lower()
        if scheme == "basic":
            return self._basic(credentials)
        if scheme == "bearer":
            return self._bearer(credentials)
        raise AuthError(f"unsupported authentication scheme: {scheme!r}")

    def _basic(self, credentials: str) -> str:
        try:
            decoded = base64.b64decode(credentials).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError) as exc:
            raise AuthError("malformed Basic credentials") from exc
        username, _, token = decoded.partition(":")
        if self.credentials.tokens.get(token) == username:
            return username
        raise AuthError("invalid username or token")

    def _bearer(self, token: str) -> str:
        if token in self.credentials.tokens:
            return self.credentials.tokens[token]
        if token in self._issued:
            return self._issued[token]
        raise AuthError("invalid bearer token")
