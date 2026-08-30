from __future__ import annotations

import hashlib
import io
import os
import subprocess
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.core.security import hash_password
from app.db.models import (
    AudioAsset,
    Export,
    MediaAsset,
    MediaAssignment,
    Project,
    RenderJob,
    TranscriptSegment,
    User,
)
from app.db.session import async_session_factory, engine
from app.domain.projects import activity_expiry
from app.services.credits import credit_balance, grant_purchase
from app.services.deletion import delete_account
from app.storage.s3 import S3ObjectStorage
from app.workers.render_tasks import _render_project

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1", reason="requires migrated PostgreSQL and MinIO"
)


@pytest_asyncio.fixture(autouse=True)
async def dispose_connections() -> AsyncIterator[None]:
    yield
    await engine.dispose()


def fixtures(tmp_path: Path) -> tuple[bytes, bytes]:
    voice = tmp_path / "voice.m4a"
    photo = tmp_path / "photo.png"
    subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=330:duration=2",
            "-c:a",
            "aac",
            str(voice),
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
            "color=c=#9b725a:s=720x1280",
            "-frames:v",
            "1",
            str(photo),
        ],
        check=True,
    )
    return voice.read_bytes(), photo.read_bytes()


async def seeded_job(
    storage: S3ObjectStorage, voice: bytes, photo: bytes, tier: str, with_assignment: bool = True
) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID]:
    async with async_session_factory() as db:
        user = User(
            email=f"render-{uuid.uuid4()}@example.test", password_hash=hash_password("password-123")
        )
        db.add(user)
        await db.flush()
        now = datetime.now(UTC)
        project = Project(
            user_id=user.id,
            status="editing",
            duration_limit_seconds=15,
            template_id="clean-story",
            last_activity_at=now,
            expires_at=activity_expiry(now),
        )
        db.add(project)
        await db.flush()
        voice_key = f"users/{user.id}/projects/{project.id}/audio/cleaned.m4a"
        photo_key = f"users/{user.id}/projects/{project.id}/media/photo.png"
        storage.put_private(voice_key, io.BytesIO(voice), "audio/mp4")
        storage.put_private(photo_key, io.BytesIO(photo), "image/png")
        db.add(
            AudioAsset(
                project_id=project.id,
                kind="cleaned",
                object_key=voice_key,
                original_filename="cleaned.m4a",
                content_type="audio/mp4",
                size_bytes=len(voice),
                duration_ms=2000,
                trim_start_ms=0,
                trim_end_ms=2000,
                analysis={},
                checksum_sha256=hashlib.sha256(voice).hexdigest(),
            )
        )
        media = MediaAsset(
            project_id=project.id,
            kind="photo",
            position=0,
            object_key=photo_key,
            original_filename="photo.png",
            content_type="image/png",
            size_bytes=len(photo),
            width=720,
            height=1280,
            duration_ms=None,
            checksum_sha256=hashlib.sha256(photo).hexdigest(),
        )
        db.add(media)
        segment = TranscriptSegment(
            project_id=project.id,
            position=0,
            start_ms=0,
            end_ms=2000,
            text="سلام دنیا",
            original_text="سلام دنیا",
            confidence=Decimal("0.95"),
        )
        db.add(segment)
        await db.flush()
        if with_assignment:
            db.add(
                MediaAssignment(
                    segment_id=segment.id,
                    media_asset_id=media.id,
                    source="automatic",
                    clip_offset_ms=0,
                )
            )
        job = RenderJob(
            project_id=project.id,
            kind=tier,
            status="queued",
            idempotency_key=str(uuid.uuid4()),
            progress=0,
            attempt_count=0,
            input_revision=hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest(),
        )
        db.add(job)
        if tier == "paid":
            await grant_purchase(db, user.id, uuid.uuid4(), 1)
        await db.commit()
        return job.id, user.id, project.id


@pytest.mark.asyncio
@pytest.mark.integration
async def test_free_paid_and_failed_render_credit_invariants(tmp_path: Path) -> None:
    storage = S3ObjectStorage()
    storage.ensure_bucket()
    voice, photo = fixtures(tmp_path)
    free_job, free_user, _ = await seeded_job(storage, voice, photo, "free")
    paid_job, paid_user, _ = await seeded_job(storage, voice, photo, "paid")
    failed_job, failed_user, _ = await seeded_job(
        storage, voice, photo, "paid", with_assignment=False
    )
    assert (await _render_project(free_job))["status"] == "succeeded"
    assert (await _render_project(paid_job))["status"] == "succeeded"
    assert (await _render_project(failed_job))["status"] == "failed"
    async with async_session_factory() as db:
        free_export = await db.scalar(
            select(Export).join(RenderJob).where(RenderJob.id == free_job)
        )
        paid_export = await db.scalar(
            select(Export).join(RenderJob).where(RenderJob.id == paid_job)
        )
        assert free_export and free_export.watermarked and free_export.width == 720
        assert paid_export and not paid_export.watermarked and paid_export.width == 1080
        assert await credit_balance(db, paid_user) == 0
        assert await credit_balance(db, failed_user) == 1
        for user_id in (free_user, paid_user, failed_user):
            await delete_account(db, storage, user_id)
