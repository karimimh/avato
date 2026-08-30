from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MediaProbe:
    duration_ms: int
    width: int
    height: int
    has_audio: bool
    has_video: bool


def probe_bytes(payload: bytes, suffix: str) -> MediaProbe:
    with tempfile.NamedTemporaryFile(suffix=suffix) as temporary:
        temporary.write(payload)
        temporary.flush()
        completed = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration:stream=codec_type,width,height",
                "-of",
                "json",
                temporary.name,
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
    data: dict[str, Any] = json.loads(completed.stdout)
    streams: list[dict[str, Any]] = data.get("streams", [])
    video: dict[str, Any] = next(
        (stream for stream in streams if stream.get("codec_type") == "video"), {}
    )
    duration = float(data.get("format", {}).get("duration", 0) or 0)
    return MediaProbe(
        duration_ms=round(duration * 1000),
        width=int(video.get("width", 0) or 0),
        height=int(video.get("height", 0) or 0),
        has_audio=any(stream.get("codec_type") == "audio" for stream in streams),
        has_video=bool(video),
    )


def suffix_for_content_type(content_type: str) -> str:
    return {
        "audio/mpeg": ".mp3",
        "audio/mp4": ".m4a",
        "audio/wav": ".wav",
        "audio/webm": ".webm",
        "audio/ogg": ".ogg",
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/heic": ".heic",
        "image/heif": ".heif",
        "video/mp4": ".mp4",
        "video/quicktime": ".mov",
        "video/webm": ".webm",
    }[content_type]
