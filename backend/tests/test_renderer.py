from pathlib import Path

import pytest

from app.media.renderer import (
    RenderRequest,
    SubtitleCue,
    build_ffmpeg_command,
    render_video,
    write_ass,
)


def test_template_commands_are_distinct_and_watermark_rule_is_explicit(tmp_path: Path) -> None:
    commands: list[str] = []
    for template in ("clean-story", "dynamic-voice", "memory-film"):
        request = RenderRequest(
            template_id=template,
            media_paths=[tmp_path / "photo.jpg"],
            section_durations_ms=[2000],
            narration_path=tmp_path / "voice.wav",
            output_path=tmp_path / f"{template}.mp4",
            subtitles=[SubtitleCue(0, 1800, "سلام دنیا")],
        )
        ass = tmp_path / f"{template}.ass"
        write_ass(request, ass)
        command = " ".join(build_ffmpeg_command(request, ass))
        assert "drawtext=text='AVATO'" in command
        commands.append(command)
    assert len(set(commands)) == 3

    paid_request = RenderRequest(
        template_id="clean-story",
        media_paths=[tmp_path / "photo.jpg"],
        section_durations_ms=[2000],
        narration_path=tmp_path / "voice.wav",
        output_path=tmp_path / "paid.mp4",
        subtitles=[],
        paid=True,
    )
    assert "drawtext=text='AVATO'" not in " ".join(
        build_ffmpeg_command(paid_request, tmp_path / "paid.ass")
    )


@pytest.mark.integration
@pytest.mark.parametrize("template", ["clean-story", "dynamic-voice", "memory-film"])
def test_each_template_is_vertical_decodable_and_has_audio(tmp_path: Path, template: str) -> None:
    import subprocess

    photo = tmp_path / "photo.png"
    voice = tmp_path / "voice.wav"
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "color=c=#9b725a:s=360x640",
            "-frames:v",
            "1",
            str(photo),
        ],
        check=True,
    )
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=2",
            str(voice),
        ],
        check=True,
    )
    result = render_video(
        RenderRequest(
            template_id=template,
            media_paths=[photo],
            section_durations_ms=[2000],
            narration_path=voice,
            output_path=tmp_path / f"{template}.mp4",
            subtitles=[SubtitleCue(0, 1800, "سلام دنیا")],
            width=360,
            height=640,
        )
    )
    assert (result.width, result.height) == (360, 640)
    assert 1900 <= result.duration_ms <= 2100
    assert result.has_audio and result.watermarked
