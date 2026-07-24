"""Static status banners for the Telegram mirror.

Each ticket status (and the ``blocked`` flag) has a pre-rendered banner PNG
shipped under ``assets/status_<name>.png``. The mirror sends the matching banner
as a photo with the ticket details as the caption — there is **no runtime image
rendering**, only loading the committed PNG bytes.
"""
from __future__ import annotations

import importlib.resources

from jira_nano.models import Ticket


def banner_bytes(name: str) -> bytes | None:
    """Return the bytes of the ``status_<name>.png`` banner, or ``None`` if absent."""
    res = importlib.resources.files("jira_nano.telegram").joinpath(
        "assets", f"status_{name}.png"
    )
    return res.read_bytes() if res.is_file() else None


def banner_for(ticket: Ticket) -> bytes | None:
    """Return the banner matching the ticket's state (``blocked`` takes precedence)."""
    return banner_bytes("blocked") if ticket.blocked else banner_bytes(str(ticket.status))
