from __future__ import annotations

import asyncio
import hashlib
import io
import tempfile
import uuid
from decimal import Decimal
from pathlib import Path

from celery import Task
from sqlalchemy import delete, select

from app.core.config import settings
from app.db.models import AudioAsset, Project, TranscriptSegment, TranscriptWord
from app.db.session import async_session_factory, engine
from app.media.audio import analyze_audio, clean_audio
from app.storage.s3 import S3ObjectStorage
from app.transcription.whisper import FasterWhisperTranscriber
from app.workers.celery_app import celery_app


@celery_app.task(name="avato.process_audio", bind=True, max_retries=2)  # type: ignore[untyped-decorator]
def process_audio_task(self: Task, audio_id: str) -> dict[str, object]:
    try:
        return asyncio.run(_process_audio_isolated(uuid.UUID(audio_id)))
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            asyncio.run(_mark_audio_failed_isolated(uuid.UUID(audio_id)))
            raise
        raise self.retry(exc=exc, countdown=10) from exc


async def _process_audio_isolated(audio_id: uuid.UUID) -> dict[str, object]:
    try:
        return await _process_audio(audio_id)
    finally:
        await engine.dispose()


async def _mark_audio_failed_isolated(audio_id: uuid.UUID) -> None:
    try:
        await _mark_audio_failed(audio_id)
    finally:
        await engine.dispose()


async def _mark_audio_failed(audio_id: uuid.UUID) -> None:
    async with async_session_factory() as db:
        original = await db.scalar(select(AudioAsset).where(AudioAsset.id == audio_id))
        if original is None:
            return
        project = await db.scalar(select(Project).where(Project.id == original.project_id))
        if project is not None:
            project.status = "failed"
            await db.commit()


async def _process_audio(audio_id: uuid.UUID) -> dict[str, object]:
    object_storage = S3ObjectStorage()
    async with async_session_factory() as db:
        original = await db.scalar(select(AudioAsset).where(AudioAsset.id == audio_id))
        if original is None:
            return {"status": "missing"}
        project = await db.scalar(select(Project).where(Project.id == original.project_id))
        if project is None:
            return {"status": "missing"}
        existing = await db.scalar(
            select(AudioAsset).where(
                AudioAsset.project_id == project.id, AudioAsset.kind == "cleaned"
            )
        )
        source_fingerprint = (
            f"{original.checksum_sha256}:{original.trim_start_ms}:"
            f"{original.trim_end_ms or original.duration_ms}"
        )
        if existing and existing.analysis.get("source_fingerprint") == source_fingerprint:
            return {"status": "already_processed", "audio_id": str(existing.id)}
        project.status = "transcribing"
        await db.commit()
        processing_project_id = project.id
        processing_audio_id = original.id
        processing_user_id = project.user_id

        with tempfile.TemporaryDirectory(prefix="avato-audio-") as directory:
            workdir = Path(directory)
            source = workdir / "original"
            cleaned = workdir / "cleaned.m4a"
            source.write_bytes(object_storage.read(original.object_key))
            clean_audio(
                source,
                cleaned,
                original.trim_start_ms,
                original.trim_end_ms or original.duration_ms,
            )
            analysis = analyze_audio(cleaned)
            result = FasterWhisperTranscriber(
                settings.whisper_model,
                settings.whisper_device,
                settings.whisper_compute_type,
            ).transcribe(cleaned)
            payload = cleaned.read_bytes()
            key = (
                f"users/{processing_user_id}/projects/{processing_project_id}/audio/"
                f"cleaned-{processing_audio_id}.m4a"
            )
            stored = object_storage.put_private(key, io.BytesIO(payload), "audio/mp4")

        # Model inference can take minutes on the first run. Account deletion or
        # another trim may legitimately happen while no database lock is held.
        # Revalidate after inference so a completed job never resurrects objects
        # or writes children for a project that disappeared meanwhile.
        await db.rollback()
        current_project = await db.scalar(
            select(Project)
            .where(Project.id == processing_project_id)
            .execution_options(populate_existing=True)
        )
        current_original = await db.scalar(
            select(AudioAsset)
            .where(AudioAsset.id == processing_audio_id)
            .execution_options(populate_existing=True)
        )
        if current_project is None or current_original is None:
            object_storage.delete(stored.key)
            return {"status": "deleted_during_processing"}
        current_fingerprint = (
            f"{current_original.checksum_sha256}:{current_original.trim_start_ms}:"
            f"{current_original.trim_end_ms or current_original.duration_ms}"
        )
        if current_fingerprint != source_fingerprint:
            object_storage.delete(stored.key)
            return {"status": "superseded"}
        project = current_project
        original = current_original
        existing = await db.scalar(
            select(AudioAsset).where(
                AudioAsset.project_id == project.id, AudioAsset.kind == "cleaned"
            )
        )
        if existing:
            object_storage.delete(existing.object_key)
            await db.delete(existing)
            await db.flush()
        cleaned_asset = AudioAsset(
            project_id=project.id,
            kind="cleaned",
            object_key=stored.key,
            original_filename="cleaned-narration.m4a",
            content_type="audio/mp4",
            size_bytes=stored.size,
            duration_ms=analysis.duration_ms,
            trim_start_ms=0,
            trim_end_ms=analysis.duration_ms,
            analysis={
                "source_checksum": original.checksum_sha256,
                "source_fingerprint": source_fingerprint,
                "mean_volume_db": analysis.mean_volume_db,
                "peak_volume_db": analysis.peak_volume_db,
                "warning": analysis.warning,
                "language": result.language,
            },
            checksum_sha256=hashlib.sha256(payload).hexdigest(),
        )
        db.add(cleaned_asset)
        await db.execute(
            delete(TranscriptSegment).where(TranscriptSegment.project_id == project.id)
        )
        for position, segment in enumerate(result.segments):
            record = TranscriptSegment(
                project_id=project.id,
                position=position,
                start_ms=segment.start_ms,
                end_ms=segment.end_ms,
                text=segment.text,
                original_text=segment.text,
                confidence=Decimal(str(round(segment.confidence, 4))),
            )
            db.add(record)
            await db.flush()
            for word_position, word in enumerate(segment.words):
                db.add(
                    TranscriptWord(
                        segment_id=record.id,
                        position=word_position,
                        start_ms=word.start_ms,
                        end_ms=word.end_ms,
                        text=word.text,
                        confidence=Decimal(str(round(word.confidence, 4))),
                    )
                )
        project.status = "editing"
        project.current_step = "media"
        await db.commit()
        return {"status": "processed", "segments": len(result.segments)}
