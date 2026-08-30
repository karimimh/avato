import subprocess
from pathlib import Path

import pytest

from app.media.audio import analyze_audio, clean_audio


@pytest.mark.integration
def test_audio_cleanup_trims_normalizes_and_remains_decodable(tmp_path: Path) -> None:
    source = tmp_path / "source.wav"
    cleaned = tmp_path / "cleaned.m4a"
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=300:duration=3",
            str(source),
        ],
        check=True,
    )
    clean_audio(source, cleaned, 250, 2500)
    analysis = analyze_audio(cleaned)
    assert 1900 <= analysis.duration_ms <= 2400
    assert analysis.mean_volume_db is not None
    assert analysis.peak_volume_db is not None
