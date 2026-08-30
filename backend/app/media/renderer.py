# ASS format declarations are intentionally kept as exact single lines.
# ruff: noqa: E501

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SubtitleCue:
    start_ms: int
    end_ms: int
    text: str


@dataclass(frozen=True)
class RenderRequest:
    template_id: str
    media_paths: list[Path]
    section_durations_ms: list[int]
    narration_path: Path
    output_path: Path
    subtitles: list[SubtitleCue]
    paid: bool = False
    title: str | None = None
    music_path: Path | None = None
    width: int = 1080
    height: int = 1920


@dataclass(frozen=True)
class RenderResult:
    output_path: Path
    width: int
    height: int
    duration_ms: int
    has_audio: bool
    watermarked: bool


TEMPLATE_VIDEO_FILTERS = {
    "clean-story": "eq=saturation=0.95:contrast=1.02",
    "dynamic-voice": "eq=saturation=1.25:contrast=1.08",
    "memory-film": "eq=saturation=0.78:brightness=0.025,vignette=PI/5",
}

TEMPLATE_STYLES = {
    "clean-story": ("&H00FFFFFF", "&H8A000000", 2, 72),
    "dynamic-voice": ("&H005BDEFF", "&HA0000000", 2, 92),
    "memory-film": ("&H00E9D7C3", "&H7A28160C", 2, 68),
}


def _ass_time(milliseconds: int) -> str:
    total_centiseconds = max(0, milliseconds // 10)
    hours, remaining = divmod(total_centiseconds, 360_000)
    minutes, remaining = divmod(remaining, 6_000)
    seconds, centiseconds = divmod(remaining, 100)
    return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"


def _ass_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}").replace("\n", "\\N")


def write_ass(request: RenderRequest, path: Path) -> None:
    primary, back, outline, font_size = TEMPLATE_STYLES[request.template_id]
    margin_v = round(request.height * 0.105)
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {request.width}
PlayResY: {request.height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,DejaVu Sans,{font_size},{primary},{primary},&H50000000,{back},-1,0,0,0,100,100,0,0,3,{outline},0,2,70,70,{margin_v},1
Style: Title,DejaVu Sans,{round(font_size * 1.35)},&H00FFFFFF,&H00FFFFFF,&H60000000,&H78000000,-1,0,0,0,100,100,0,0,3,2,0,8,60,60,150,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
    lines = [header]
    if request.title:
        lines.append(
            f"Dialogue: 0,0:00:00.00,0:00:02.50,Title,,0,0,0,,{_ass_escape(request.title)}\n"
        )
    for cue in request.subtitles:
        lines.append(
            "Dialogue: 0,"
            f"{_ass_time(cue.start_ms)},{_ass_time(cue.end_ms)},Default,,0,0,0,,"
            f"{_ass_escape(cue.text)}\n"
        )
    path.write_text("".join(lines), encoding="utf-8")


def build_ffmpeg_command(request: RenderRequest, subtitle_path: Path) -> list[str]:
    if request.template_id not in TEMPLATE_VIDEO_FILTERS:
        raise ValueError("unknown template")
    if not request.media_paths or len(request.media_paths) != len(request.section_durations_ms):
        raise ValueError("every visual section requires one media path and duration")
    if any(duration < 500 for duration in request.section_durations_ms):
        raise ValueError("visual sections must be at least 500ms")

    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]
    for path, duration in zip(request.media_paths, request.section_durations_ms, strict=True):
        if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            command.extend(["-loop", "1", "-t", f"{duration / 1000:.3f}", "-i", str(path)])
        else:
            command.extend(["-stream_loop", "-1", "-t", f"{duration / 1000:.3f}", "-i", str(path)])
    narration_index = len(request.media_paths)
    command.extend(["-i", str(request.narration_path)])
    music_index = narration_index + 1
    if request.music_path:
        command.extend(["-stream_loop", "-1", "-i", str(request.music_path)])

    filters: list[str] = []
    video_labels: list[str] = []
    template_filter = TEMPLATE_VIDEO_FILTERS[request.template_id]
    for index, duration in enumerate(request.section_durations_ms):
        fade = ""
        if request.template_id == "memory-film":
            fade_out = max(0.6, duration / 1000 - 0.45)
            fade = f",fade=t=in:st=0:d=0.35,fade=t=out:st={fade_out:.3f}:d=0.35"
        filters.append(
            f"[{index}:v]scale={request.width}:{request.height}:force_original_aspect_ratio=increase,"
            f"crop={request.width}:{request.height},setsar=1,fps=30,{template_filter}{fade}[v{index}]"
        )
        video_labels.append(f"[v{index}]")
    filters.append(f"{''.join(video_labels)}concat=n={len(video_labels)}:v=1:a=0[vcat]")

    ass_path = str(subtitle_path).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
    video_source = "vcat"
    if request.template_id == "dynamic-voice":
        filters.append(
            f"[{narration_index}:a]asplit=2[voice][waveaudio];"
            f"[waveaudio]showwaves=s={request.width - 120}x110:mode=line:colors=0xFFD35B@0.88,"
            "format=rgba[wave]"
        )
        filters.append("[vcat][wave]overlay=(W-w)/2:H-h-230[vstyled]")
        filters.append("[voice]loudnorm=I=-16:TP=-1.5:LRA=11[narr]")
        video_source = "vstyled"
    else:
        filters.append(f"[{narration_index}:a]loudnorm=I=-16:TP=-1.5:LRA=11[narr]")

    filters.append(f"[{video_source}]subtitles=filename='{ass_path}'[vsub]")
    if request.paid:
        filters.append("[vsub]null[vout]")
    else:
        filters.append(
            "[vsub]drawtext=text='AVATO':fontcolor=white@0.78:fontsize=h/45:"
            "box=1:boxcolor=black@0.30:boxborderw=10:x=w-tw-32:y=32[vout]"
        )

    total_seconds = sum(request.section_durations_ms) / 1000
    if request.music_path:
        fade_out = max(0.0, total_seconds - 1.2)
        filters.append(
            f"[{music_index}:a]volume=0.12,afade=t=in:st=0:d=0.8,"
            f"afade=t=out:st={fade_out:.3f}:d=1.2[music]"
        )
        filters.append("[narr][music]amix=inputs=2:duration=first:dropout_transition=1[aout]")
    else:
        filters.append("[narr]anull[aout]")

    command.extend(
        [
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[vout]",
            "-map",
            "[aout]",
            "-t",
            f"{total_seconds:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20" if request.paid else "26",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k" if request.paid else "128k",
            "-movflags",
            "+faststart",
            str(request.output_path),
        ]
    )
    return command


def probe_video(path: Path) -> RenderResult:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration:stream=codec_type,width,height",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    probe = json.loads(completed.stdout)
    video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
    return RenderResult(
        output_path=path,
        width=int(video["width"]),
        height=int(video["height"]),
        duration_ms=round(float(probe["format"]["duration"]) * 1000),
        has_audio=any(stream["codec_type"] == "audio" for stream in probe["streams"]),
        watermarked=False,
    )


def render_video(request: RenderRequest) -> RenderResult:
    request.output_path.parent.mkdir(parents=True, exist_ok=True)
    subtitle_path = request.output_path.with_suffix(".ass")
    try:
        write_ass(request, subtitle_path)
        subprocess.run(build_ffmpeg_command(request, subtitle_path), check=True)
        result = probe_video(request.output_path)
        return RenderResult(
            output_path=result.output_path,
            width=result.width,
            height=result.height,
            duration_ms=result.duration_ms,
            has_audio=result.has_audio,
            watermarked=not request.paid,
        )
    finally:
        subtitle_path.unlink(missing_ok=True)
