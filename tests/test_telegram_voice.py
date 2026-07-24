"""Voice-message transcription — JN-43."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pygit2
import pytest

from conftest import FakeGateway
from jira_nano.service import TicketService
from jira_nano.telegram.topics import ensure_topic
from jira_nano.telegram.transcribe import (
    CloudTranscriber,
    LocalWhisperTranscriber,
    build_transcriber,
)
from jira_nano.telegram.voice import transcribe_voice
from jira_nano.users import UserDirectory


class FakeTranscriber:
    """In-memory STT backend that records its calls (never touches heavy libs)."""

    def __init__(self, text: str = "hello from voice") -> None:
        self._text = text
        self.calls: list[tuple[bytes, str | None]] = []

    def transcribe(self, audio: bytes, mime: str | None = None) -> str:
        self.calls.append((audio, mime))
        return self._text


@pytest.fixture
def service(tmp_path: Path) -> TicketService:
    pygit2.init_repository(str(tmp_path), bare=False)
    cfg = tmp_path / ".jira_nano"
    cfg.mkdir()
    (cfg / "users.yaml").write_text("korkin25:\n  telegram: '@korkin25'\n")
    return TicketService(tmp_path)


def _directory(service: TicketService) -> UserDirectory:
    return UserDirectory.load(service.paths.config_dir)


def test_transcribe_voice_writes_comment(service: TicketService, gateway: FakeGateway) -> None:
    t = service.create(title="Fix", reporter="e")
    topic_id = asyncio.run(ensure_topic(service, gateway, t.id))
    transcriber = FakeTranscriber()

    result = transcribe_voice(
        service, _directory(service), transcriber, b"audiobytes", "audio/ogg", topic_id, "@korkin25"
    )

    assert result == t.id
    assert transcriber.calls == [(b"audiobytes", "audio/ogg")]
    comment = service.get(t.id).comments[-1]
    assert comment.body == "🎙 hello from voice"
    assert comment.source == "telegram"
    assert comment.author == "korkin25"


def test_transcribe_voice_unknown_topic(service: TicketService) -> None:
    result = transcribe_voice(
        service, _directory(service), FakeTranscriber(), b"x", None, 999, "@korkin25"
    )
    assert result is None


def test_transcribe_voice_empty_transcript(service: TicketService, gateway: FakeGateway) -> None:
    t = service.create(title="Fix", reporter="e")
    topic_id = asyncio.run(ensure_topic(service, gateway, t.id))

    result = transcribe_voice(
        service, _directory(service), FakeTranscriber(text=""), b"x", None, topic_id, "@korkin25"
    )

    assert result is None
    assert service.get(t.id).comments == []


def test_transcribe_voice_unknown_user_falls_back(
    service: TicketService, gateway: FakeGateway
) -> None:
    t = service.create(title="Fix", reporter="e")
    topic_id = asyncio.run(ensure_topic(service, gateway, t.id))

    transcribe_voice(
        service, _directory(service), FakeTranscriber(), b"x", None, topic_id, "@stranger"
    )

    assert service.get(t.id).comments[-1].author == "stranger"


def test_build_transcriber_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JIRA_NANO_STT", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert isinstance(build_transcriber(), LocalWhisperTranscriber)


def test_build_transcriber_cloud(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JIRA_NANO_STT", "cloud")
    assert isinstance(build_transcriber(), CloudTranscriber)


def test_build_transcriber_local_forces_local(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JIRA_NANO_STT", "local")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")  # ignored when local is forced
    assert isinstance(build_transcriber(), LocalWhisperTranscriber)


def test_build_transcriber_auto_prefers_cloud_with_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JIRA_NANO_STT", raising=False)  # auto
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert isinstance(build_transcriber(), CloudTranscriber)
