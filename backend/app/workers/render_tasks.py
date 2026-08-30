from __future__ import annotations

import asyncio
import hashlib
import io
import subprocess
import tempfile
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from celery import Task
from sqlalchemy import select

from app.db.models import (
    AudioAsset,
    Export,
    MediaAsset,
    MediaAssignment,
    MusicTrack,
    Project,
    RenderJob,
    TranscriptSegment,
    User,
)
from app.db.session import async_session_factory, engine
from app.media.probe import suffix_for_content_type
from app.media.renderer import RenderRequest, SubtitleCue, render_video
from app.services.credits import charge_successful_export
from app.storage.s3 import S3ObjectStorage
from app.workers.celery_app import celery_app


@celery_app.task(name="avato.render_project", bind=True)  # type: ignore[untyped-decorator]
def render_project_task(self: Task, job_id: str) -> dict[str, object]:
    del self
    return asyncio.run(_render_project_isolated(uuid.UUID(job_id)))


async def _render_project_isolated(job_id: uuid.UUID) -> dict[str, object]:
    try:
        return await _render_project(job_id)
    finally:
        await engine.dispose()


async def _mark_failed(job_id: uuid.UUID, code: str, detail: str) -> None:
    async with async_session_factory() as db:
        job = await db.get(RenderJob, job_id)
        if job:
            job.status = "failed"
            job.error_code = code
            job.error_detail = detail[:1000]
            job.finished_at = datetime.now(UTC)
            project = await db.get(Project, job.project_id)
            if project:
                project.status = "failed"
            await db.commit()


async def _render_project(job_id: uuid.UUID) -> dict[str, object]:
    object_storage = S3ObjectStorage()
    output_key: str | None = None
    cover_key: str | None = None
    try:
        async with async_session_factory() as db:
            job = await db.scalar(select(RenderJob).where(RenderJob.id == job_id).with_for_update())
            if job is None:
                return {"status": "missing"}
            existing_export = await db.scalar(select(Export).where(Export.render_job_id == job.id))
            if existing_export:
                return {"status": "already_complete", "export_id": str(existing_export.id)}
            if job.status == "cancelled":
                return {"status": "cancelled"}
            project = await db.get(Project, job.project_id)
            if project is None:
                return {"status": "missing"}
            job.status = "running"
            job.attempt_count += 1
            job.progress = 5
            job.started_at = datetime.now(UTC)
            project.status = "rendering"
            await db.commit()

            narration = await db.scalar(
                select(AudioAsset).where(
                    AudioAsset.project_id == project.id, AudioAsset.kind == "cleaned"
                )
            )
            segments = list(
                (
                    await db.scalars(
                        select(TranscriptSegment)
                        .where(TranscriptSegment.project_id == project.id)
                        .order_by(TranscriptSegment.position)
                    )
                ).all()
            )
            if narration is None or not segments:
                raise ValueError("cleaned narration and transcript are required")
            assignments: list[tuple[TranscriptSegment, MediaAsset]] = []
            for segment in segments:
                assignment = await db.scalar(
                    select(MediaAssignment).where(MediaAssignment.segment_id == segment.id)
                )
                if assignment is None:
                    raise ValueError("every transcript segment requires media")
                media = await db.get(MediaAsset, assignment.media_asset_id)
                if media is None or media.project_id != project.id:
                    raise ValueError("assigned media is missing")
                assignments.append((segment, media))
            music = (
                await db.get(MusicTrack, project.music_track_id) if project.music_track_id else None
            )
            user = await db.get(User, project.user_id)
            if user is None:
                raise ValueError("project owner is missing")

            with tempfile.TemporaryDirectory(prefix="avato-render-") as directory:
                workdir = Path(directory)
                narration_path = workdir / "narration.m4a"
                narration_path.write_bytes(object_storage.read(narration.object_key))
                media_paths: list[Path] = []
                for index, (_, media) in enumerate(assignments):
                    path = workdir / f"media-{index}{suffix_for_content_type(media.content_type)}"
                    path.write_bytes(object_storage.read(media.object_key))
                    media_paths.append(path)
                music_path: Path | None = None
                if music:
                    music_path = workdir / "music.wav"
                    music_path.write_bytes(object_storage.read(music.object_key))
                output = workdir / "output.mp4"
                paid = job.kind == "paid"
                width, height = (1080, 1920) if paid else (720, 1280)
                result = render_video(
                    RenderRequest(
                        template_id=project.template_id,
                        media_paths=media_paths,
                        section_durations_ms=[
                            segment.end_ms - segment.start_ms for segment, _ in assignments
                        ],
                        narration_path=narration_path,
                        output_path=output,
                        subtitles=[
                            SubtitleCue(segment.start_ms, segment.end_ms, segment.text)
                            for segment in segments
                        ],
                        paid=paid,
                        title=project.title,
                        music_path=music_path,
                        width=width,
                        height=height,
                    )
                )
                cover = workdir / "cover.jpg"
                subprocess.run(
                    [
                        "ffmpeg",
                        "-loglevel",
                        "error",
                        "-y",
                        "-i",
                        str(output),
                        "-frames:v",
                        "1",
                        str(cover),
                    ],
                    check=True,
                    timeout=60,
                )
                output_payload = output.read_bytes()
                cover_payload = cover.read_bytes()
                await db.refresh(job)
                if job.status == "cancelled":
                    return {"status": "cancelled"}
                output_key = f"users/{user.id}/projects/{project.id}/exports/{job.id}.mp4"
                cover_key = f"users/{user.id}/projects/{project.id}/exports/{job.id}-cover.jpg"
                stored_output = object_storage.put_private(
                    output_key, io.BytesIO(output_payload), "video/mp4"
                )
                object_storage.put_private(cover_key, io.BytesIO(cover_payload), "image/jpeg")

            await db.refresh(job)
            if job.status == "cancelled":
                object_storage.delete(output_key)
                object_storage.delete(cover_key)
                return {"status": "cancelled"}

            export = Export(
                project_id=project.id,
                render_job_id=job.id,
                tier=job.kind,
                object_key=output_key,
                cover_object_key=cover_key,
                width=result.width,
                height=result.height,
                duration_ms=result.duration_ms,
                size_bytes=stored_output.size,
                watermarked=result.watermarked,
                checksum_sha256=hashlib.sha256(output_payload).hexdigest(),
                reexport_until=datetime.now(UTC) + timedelta(days=7) if paid else None,
            )
            db.add(export)
            await db.flush()
            if paid:
                await charge_successful_export(db, user.id, project.id, export.id)
            else:
                locked_user = await db.scalar(
                    select(User).where(User.id == user.id).with_for_update()
                )
                if locked_user is None or locked_user.trial_used_at is not None:
                    raise ValueError("free trial has already been used")
                locked_user.trial_used_at = datetime.now(UTC)
            job.status = "succeeded"
            job.progress = 100
            job.finished_at = datetime.now(UTC)
            project.status = "ready"
            await db.commit()
            return {"status": "succeeded", "export_id": str(export.id)}
    except Exception as exc:
        if output_key:
            object_storage.delete(output_key)
        if cover_key:
            object_storage.delete(cover_key)
        await _mark_failed(job_id, "render_failed", str(exc))
        return {"status": "failed", "error": str(exc)}
