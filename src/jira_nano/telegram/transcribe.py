"""Speech-to-text backends for voice-message transcription (JN-43).

A voice/audio message posted in a ticket's forum topic is transcribed and pulled
back into the ticket as a comment. The backend is pluggable: the default runs a
local Whisper model (``faster-whisper``, installed on demand via
``pip install "jira-nano[voice]"``), and an optional cloud backend uses OpenAI.

The heavy / optional third-party libraries are imported **lazily** inside
:meth:`transcribe`, so importing this module — and instantiating a backend — never
requires them. ``build_transcriber`` therefore stays cheap and import-safe.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Any, Protocol


class Transcriber(Protocol):
    """A pluggable speech-to-text backend."""

    def transcribe(self, audio: bytes, mime: str | None = None) -> str:
        """Transcribe ``audio`` (raw bytes; ``mime`` is a content-type hint)."""
        ...


def _suffix_for(mime: str | None) -> str:
    """Derive a temp-file suffix from an audio ``mime`` type (default ``.ogg``)."""
    if mime and "/" in mime:
        subtype = mime.split("/", 1)[1].split(";", 1)[0].strip()
        if subtype:
            return f".{subtype}"
    return ".ogg"


class LocalWhisperTranscriber:
    """Default backend: a locally-run Whisper model via ``faster-whisper``."""

    def __init__(self, model: str | None = None) -> None:
        """Store the model name; the model handle is created lazily on first use."""
        self._model_name = model or os.environ.get("JIRA_NANO_WHISPER_MODEL", "base")
        self._model: Any = None  # lazy WhisperModel handle, built on first transcribe

    def ensure_model(self) -> None:
        """Load the Whisper model now, triggering the one-time model download."""
        if self._model is not None:
            return
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:  # pragma: no cover - only without the optional extra
            raise RuntimeError(
                'faster-whisper is not installed; run: pip install "jira-nano[voice]"'
            ) from exc
        self._model = WhisperModel(self._model_name)

    def transcribe(self, audio: bytes, mime: str | None = None) -> str:
        """Transcribe ``audio`` with a locally-run Whisper model."""
        self.ensure_model()
        suffix = _suffix_for(mime)
        # ``delete=False`` so the file survives the ``with`` block for Whisper to
        # read by path; we unlink it ourselves in the ``finally``.
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio)
            path = tmp.name
        try:
            segments, _info = self._model.transcribe(path)
            return " ".join(segment.text for segment in segments).strip()
        finally:
            Path(path).unlink(missing_ok=True)


class CloudTranscriber:
    """Optional backend: OpenAI's hosted speech-to-text API."""

    def transcribe(self, audio: bytes, mime: str | None = None) -> str:
        """Transcribe ``audio`` via the OpenAI transcriptions API."""
        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover - only without the optional dep
            raise RuntimeError("openai is not installed; run: pip install openai") from exc
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not set")
        client = OpenAI()
        suffix = _suffix_for(mime)
        resp = client.audio.transcriptions.create(
            model=os.environ.get("JIRA_NANO_STT_MODEL", "whisper-1"),
            file=(f"audio{suffix}", audio),
        )
        return str(resp.text).strip()


def build_transcriber() -> Transcriber:
    """Select the STT backend from ``JIRA_NANO_STT`` (``auto`` | ``local`` | ``cloud``).

    ``auto`` (the default) uses the cloud backend when ``OPENAI_API_KEY`` is set,
    otherwise the portable local Whisper. Instantiation is cheap and import-safe:
    the heavy libraries are only imported when :meth:`Transcriber.transcribe` runs.
    """
    mode = os.environ.get("JIRA_NANO_STT", "auto").lower()
    if mode == "cloud":
        return CloudTranscriber()
    if mode == "local":
        return LocalWhisperTranscriber()
    if os.environ.get("OPENAI_API_KEY"):  # auto: prefer cloud when a key is configured
        return CloudTranscriber()
    return LocalWhisperTranscriber()


def preload() -> None:  # pragma: no cover - downloads/loads the Whisper model
    """Console entry point (``jira-nano-voice-setup``): fetch the local model once.

    Instantiates the local backend and forces the Whisper model to load so the
    (possibly large) download happens up front — after this the bot transcribes
    offline. Requires the ``[voice]`` extra.
    """
    backend = LocalWhisperTranscriber()
    backend.ensure_model()
    print(f"jira_nano: local Whisper model '{backend._model_name}' is ready")
