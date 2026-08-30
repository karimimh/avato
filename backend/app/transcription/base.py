from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class TranscriptWordResult:
    text: str
    start_ms: int
    end_ms: int
    confidence: float


@dataclass(frozen=True)
class TranscriptSegmentResult:
    text: str
    start_ms: int
    end_ms: int
    confidence: float
    words: tuple[TranscriptWordResult, ...]


@dataclass(frozen=True)
class TranscriptResult:
    language: str
    segments: tuple[TranscriptSegmentResult, ...]


class Transcriber(Protocol):
    def transcribe(self, audio_path: Path) -> TranscriptResult: ...
