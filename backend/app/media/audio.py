from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AudioAnalysis:
    duration_ms: int
    mean_volume_db: float | None
    peak_volume_db: float | None
    warning: str | None


def clean_audio(source: Path, destination: Path, start_ms: int, end_ms: int) -> None:
    if start_ms < 0 or end_ms <= start_ms or end_ms - start_ms > 60_000:
        raise ValueError("cleaned narration must be between trim bounds and at most 60 seconds")
    destination.parent.mkdir(parents=True, exist_ok=True)
    filters = (
        f"atrim=start={start_ms / 1000:.3f}:end={end_ms / 1000:.3f},asetpts=PTS-STARTPTS,"
        "silenceremove=start_periods=1:start_duration=0.15:start_threshold=-45dB:"
        "stop_periods=-1:stop_duration=1.2:stop_threshold=-45dB,"
        "afftdn=nf=-25,loudnorm=I=-16:TP=-1.5:LRA=11"
    )
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(source),
            "-vn",
            "-af",
            filters,
            "-ar",
            "48000",
            "-ac",
            "1",
            "-c:a",
            "aac",
            "-b:a",
            "128k",
            str(destination),
        ],
        check=True,
        timeout=120,
    )


def analyze_audio(path: Path) -> AudioAnalysis:
    duration_probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    duration = float(json.loads(duration_probe.stdout)["format"]["duration"])
    volume = subprocess.run(
        ["ffmpeg", "-hide_banner", "-i", str(path), "-af", "volumedetect", "-f", "null", "-"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    mean: float | None = None
    peak: float | None = None
    for line in volume.stderr.splitlines():
        if "mean_volume:" in line:
            mean = float(line.split("mean_volume:", 1)[1].split(" dB", 1)[0].strip())
        if "max_volume:" in line:
            peak = float(line.split("max_volume:", 1)[1].split(" dB", 1)[0].strip())
    warning = "too_quiet" if mean is not None and mean < -35 else None
    return AudioAnalysis(round(duration * 1000), mean, peak, warning)
