"""Create the private bucket and redistributable synthetic local music fixtures."""

from __future__ import annotations

import io
import subprocess
import tempfile
from pathlib import Path

from app.storage.s3 import S3ObjectStorage

TRACKS = {"calm-local": 220, "emotional-local": 262, "upbeat-local": 330}


def main() -> None:
    storage = S3ObjectStorage()
    storage.ensure_bucket()
    with tempfile.TemporaryDirectory(prefix="avato-music-") as directory:
        for track, frequency in TRACKS.items():
            path = Path(directory) / f"{track}.wav"
            subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    f"sine=frequency={frequency}:duration=60:sample_rate=48000",
                    "-af",
                    "volume=0.08,afade=t=in:d=2,afade=t=out:st=58:d=2",
                    "-c:a",
                    "pcm_s16le",
                    str(path),
                ],
                check=True,
                timeout=90,
            )
            storage.put_private(
                f"catalog/music/{track}.wav", io.BytesIO(path.read_bytes()), "audio/wav"
            )


if __name__ == "__main__":
    main()
