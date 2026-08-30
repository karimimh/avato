from __future__ import annotations

from pathlib import Path
from typing import Any

from app.transcription.base import (
    TranscriptResult,
    TranscriptSegmentResult,
    TranscriptWordResult,
)


class FasterWhisperTranscriber:
    """Lazy local Persian transcriber; model loading never happens in unit tests."""

    def __init__(
        self, model_name: str = "small", device: str = "cpu", compute_type: str = "int8"
    ) -> None:
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        self._model: Any = None

    def _load(self) -> Any:
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.model_name, device=self.device, compute_type=self.compute_type
            )
        return self._model

    def transcribe(self, audio_path: Path) -> TranscriptResult:
        raw_segments, info = self._load().transcribe(
            str(audio_path),
            language="fa",
            word_timestamps=True,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
            beam_size=5,
        )
        segments: list[TranscriptSegmentResult] = []
        for raw in raw_segments:
            words = tuple(
                TranscriptWordResult(
                    text=word.word.strip(),
                    start_ms=round(word.start * 1000),
                    end_ms=round(word.end * 1000),
                    confidence=max(0.0, min(1.0, float(word.probability))),
                )
                for word in (raw.words or [])
                if word.word.strip()
            )
            confidence = sum(word.confidence for word in words) / len(words) if words else 0.0
            segments.append(
                TranscriptSegmentResult(
                    text=raw.text.strip(),
                    start_ms=round(raw.start * 1000),
                    end_ms=round(raw.end * 1000),
                    confidence=confidence,
                    words=words,
                )
            )
        return TranscriptResult(language=str(info.language), segments=tuple(segments))
