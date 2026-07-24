"""Voice-message → ticket-comment core (JN-43).

The event-loop-free, unit-testable heart of voice pull-back: given raw audio, a
:class:`~jira_nano.telegram.transcribe.Transcriber` and a forum topic, it resolves
the ticket, transcribes the audio and appends the transcript as a comment. It
reuses :func:`~jira_nano.telegram.pullback.pull_back`, so author resolution, the
comment write and the git commit are shared with plain text pull-back.
"""
from __future__ import annotations

from jira_nano.service import TicketService
from jira_nano.users import UserDirectory

from .pullback import find_ticket_by_topic, pull_back
from .transcribe import Transcriber


def transcribe_voice(
    service: TicketService,
    directory: UserDirectory,
    transcriber: Transcriber,
    audio: bytes,
    mime: str | None,
    topic_id: int,
    username: str,
) -> str | None:
    """Transcribe a voice message into its ticket as a comment; return the ticket id.

    Returns ``None`` when the topic maps to no ticket or the transcript is empty
    (in which case nothing is written).
    """
    ticket_id = find_ticket_by_topic(service, topic_id)
    if ticket_id is None:
        return None
    text = transcriber.transcribe(audio, mime).strip()
    if not text:
        return None
    return pull_back(service, directory, topic_id, username, f"🎙 {text}")
