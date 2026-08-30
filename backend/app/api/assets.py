from __future__ import annotations

import io
import subprocess
import uuid
from datetime import UTC, datetime
from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Header, Request
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select, update

from app.api.dependencies import CurrentUser, Database, OwnedProject
from app.api.errors import ApiError
from app.db.models import AudioAsset, MediaAsset
from app.domain.projects import activity_expiry
from app.domain.uploads import MAX_VIDEO_BYTES, UploadRejected, validate_upload
from app.media.probe import probe_bytes, suffix_for_content_type
from app.storage.s3 import S3ObjectStorage
from app.workers.tasks import process_audio_task

router = APIRouter(prefix="/projects/{project_id}", tags=["assets"])


class AudioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    kind: str
    original_filename: str
    content_type: str
    size_bytes: int
    duration_ms: int
    trim_start_ms: int
    trim_end_ms: int | None
    analysis: dict[str, object]
    url: str | None = None


class MediaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    kind: str
    position: int
    original_filename: str
    content_type: str
    size_bytes: int
    width: int
    height: int
    duration_ms: int | None
    url: str | None = None


class MediaListResponse(BaseModel):
    items: list[MediaResponse]


class MediaOrderRequest(BaseModel):
    media_ids: list[uuid.UUID]


class AudioTrimRequest(BaseModel):
    start_ms: int
    end_ms: int


@lru_cache
def storage() -> S3ObjectStorage:
    return S3ObjectStorage()


async def bounded_body(request: Request, maximum: int = MAX_VIDEO_BYTES) -> bytes:
    chunks: list[bytes] = []
    total = 0
    async for chunk in request.stream():
        total += len(chunk)
        if total > maximum:
            raise ApiError(413, "file_too_large", "حجم فایل بیشتر از حد مجاز است.")
        chunks.append(chunk)
    return b"".join(chunks)


@router.put("/audio", response_model=AudioResponse)
async def upload_audio(
    request: Request,
    project: OwnedProject,
    db: Database,
    user: CurrentUser,
    x_filename: Annotated[str, Header(max_length=255)] = "voice-note",
) -> AudioAsset:
    content_type = request.headers.get("content-type", "application/octet-stream").split(";", 1)[0]
    payload = await bounded_body(request)
    try:
        validated = validate_upload(x_filename, content_type, len(payload), payload[:32])
    except UploadRejected as exc:
        raise ApiError(422, exc.code, exc.message_fa) from exc
    if validated.kind != "audio":
        raise ApiError(422, "audio_required", "برای این بخش یک فایل صوتی لازم است.")
    try:
        probe = probe_bytes(payload, suffix_for_content_type(content_type))
    except (subprocess.SubprocessError, ValueError, KeyError) as exc:
        raise ApiError(422, "invalid_audio", "فایل صوتی قابل خواندن نیست.") from exc
    if probe.duration_ms < 5000:
        raise ApiError(422, "audio_too_short", "ویس باید دست‌کم ۵ ثانیه باشد.")
    if probe.duration_ms > 90_000:
        raise ApiError(422, "audio_too_long", "ویس بیشتر از ۹۰ ثانیه قابل پذیرش نیست.")

    object_key = (
        f"users/{user.id}/projects/{project.id}/audio/"
        f"{uuid.uuid4()}{suffix_for_content_type(content_type)}"
    )
    object_storage = storage()
    object_storage.ensure_bucket()
    stored = object_storage.put_private(object_key, io.BytesIO(payload), content_type)
    previous = await db.scalar(
        select(AudioAsset).where(AudioAsset.project_id == project.id, AudioAsset.kind == "original")
    )
    if previous:
        object_storage.delete(previous.object_key)
        await db.delete(previous)
        await db.flush()
    asset = AudioAsset(
        project_id=project.id,
        kind="original",
        object_key=stored.key,
        original_filename=validated.filename,
        content_type=content_type,
        size_bytes=stored.size,
        duration_ms=probe.duration_ms,
        trim_start_ms=0,
        trim_end_ms=min(probe.duration_ms, project.duration_limit_seconds * 1000),
        analysis={"requires_trim": probe.duration_ms > project.duration_limit_seconds * 1000},
        checksum_sha256=stored.checksum_sha256,
    )
    db.add(asset)
    now = datetime.now(UTC)
    project.last_activity_at = now
    project.expires_at = activity_expiry(now)
    project.current_step = "transcript"
    await db.commit()
    await db.refresh(asset)
    process_audio_task.delay(str(asset.id))
    return asset


@router.get("/audio", response_model=list[AudioResponse])
async def list_audio(project: OwnedProject, db: Database) -> list[AudioResponse]:
    items = list(
        (await db.scalars(select(AudioAsset).where(AudioAsset.project_id == project.id))).all()
    )
    return [
        AudioResponse.model_validate(item).model_copy(
            update={"url": storage().presigned_get(item.object_key, 300)}
        )
        for item in items
    ]


@router.patch("/audio/{audio_id}/trim", response_model=AudioResponse)
async def trim_audio(
    audio_id: uuid.UUID,
    payload: AudioTrimRequest,
    project: OwnedProject,
    db: Database,
) -> AudioResponse:
    original = await db.scalar(
        select(AudioAsset).where(
            AudioAsset.id == audio_id,
            AudioAsset.project_id == project.id,
            AudioAsset.kind == "original",
        )
    )
    if original is None:
        raise ApiError(404, "audio_not_found", "فایل صوتی اصلی پیدا نشد.")
    if payload.start_ms < 0 or payload.end_ms > original.duration_ms:
        raise ApiError(422, "invalid_trim", "بازهٔ برش بیرون از زمان ویس است.")
    trimmed_duration = payload.end_ms - payload.start_ms
    if trimmed_duration < 5000:
        raise ApiError(422, "trim_too_short", "بخش انتخاب‌شده باید دست‌کم ۵ ثانیه باشد.")
    if trimmed_duration > project.duration_limit_seconds * 1000:
        raise ApiError(422, "trim_too_long", "بخش انتخاب‌شده از زمان پروژه طولانی‌تر است.")
    original.trim_start_ms = payload.start_ms
    original.trim_end_ms = payload.end_ms
    project.status = "transcribing"
    project.current_step = "transcript"
    now = datetime.now(UTC)
    project.last_activity_at = now
    project.expires_at = activity_expiry(now)
    await db.commit()
    process_audio_task.delay(str(original.id))
    return AudioResponse.model_validate(original).model_copy(
        update={"url": storage().presigned_get(original.object_key, 300)}
    )


@router.post("/media", response_model=MediaResponse, status_code=201)
async def upload_media(
    request: Request,
    project: OwnedProject,
    db: Database,
    user: CurrentUser,
    x_filename: Annotated[str, Header(max_length=255)] = "media",
) -> MediaAsset:
    count = int(
        await db.scalar(
            select(func.count(MediaAsset.id)).where(MediaAsset.project_id == project.id)
        )
        or 0
    )
    if count >= 12:
        raise ApiError(409, "media_limit", "حداکثر ۱۲ عکس یا کلیپ مجاز است.")
    content_type = request.headers.get("content-type", "application/octet-stream").split(";", 1)[0]
    payload = await bounded_body(request)
    try:
        validated = validate_upload(x_filename, content_type, len(payload), payload[:32])
        probe = probe_bytes(payload, suffix_for_content_type(content_type))
    except (UploadRejected, subprocess.SubprocessError, ValueError, KeyError) as exc:
        if isinstance(exc, UploadRejected):
            raise ApiError(422, exc.code, exc.message_fa) from exc
        raise ApiError(422, "invalid_media", "این فایل رسانه‌ای قابل خواندن نیست.") from exc
    if validated.kind == "audio":
        raise ApiError(422, "visual_required", "در این بخش عکس یا کلیپ لازم است.")
    if validated.kind == "clip" and (probe.duration_ms <= 0 or probe.duration_ms > 60_000):
        raise ApiError(422, "clip_duration", "کلیپ باید حداکثر ۶۰ ثانیه باشد.")
    object_key = (
        f"users/{user.id}/projects/{project.id}/media/"
        f"{uuid.uuid4()}{suffix_for_content_type(content_type)}"
    )
    object_storage = storage()
    object_storage.ensure_bucket()
    stored = object_storage.put_private(object_key, io.BytesIO(payload), content_type)
    asset = MediaAsset(
        project_id=project.id,
        kind=validated.kind,
        position=count,
        object_key=stored.key,
        original_filename=validated.filename,
        content_type=content_type,
        size_bytes=stored.size,
        width=probe.width,
        height=probe.height,
        duration_ms=probe.duration_ms if validated.kind == "clip" else None,
        checksum_sha256=stored.checksum_sha256,
    )
    db.add(asset)
    now = datetime.now(UTC)
    project.last_activity_at = now
    project.expires_at = activity_expiry(now)
    project.current_step = "style"
    await db.commit()
    await db.refresh(asset)
    return asset


@router.get("/media", response_model=MediaListResponse)
async def list_media(project: OwnedProject, db: Database) -> MediaListResponse:
    items = list(
        (
            await db.scalars(
                select(MediaAsset)
                .where(MediaAsset.project_id == project.id)
                .order_by(MediaAsset.position)
            )
        ).all()
    )
    return MediaListResponse(
        items=[
            MediaResponse.model_validate(item).model_copy(
                update={"url": storage().presigned_get(item.object_key, 300)}
            )
            for item in items
        ]
    )


@router.patch("/media/order", response_model=MediaListResponse)
async def reorder_media(
    payload: MediaOrderRequest, project: OwnedProject, db: Database
) -> MediaListResponse:
    existing = list(
        (await db.scalars(select(MediaAsset).where(MediaAsset.project_id == project.id))).all()
    )
    if len(payload.media_ids) != len(existing) or set(payload.media_ids) != {
        item.id for item in existing
    }:
        raise ApiError(422, "invalid_media_order", "فهرست ترتیب رسانه‌ها کامل یا معتبر نیست.")
    await db.execute(
        update(MediaAsset)
        .where(MediaAsset.project_id == project.id)
        .values(position=MediaAsset.position + 100)
    )
    for position, media_id in enumerate(payload.media_ids):
        await db.execute(
            update(MediaAsset).where(MediaAsset.id == media_id).values(position=position)
        )
    await db.commit()
    return await list_media(project, db)


@router.delete("/media/{media_id}", response_model=MediaListResponse)
async def delete_media(
    media_id: uuid.UUID, project: OwnedProject, db: Database
) -> MediaListResponse:
    item = await db.scalar(
        select(MediaAsset).where(MediaAsset.id == media_id, MediaAsset.project_id == project.id)
    )
    if item is None:
        raise ApiError(404, "media_not_found", "رسانه پیدا نشد.")
    deleted_position = item.position
    storage().delete(item.object_key)
    if item.thumbnail_key:
        storage().delete(item.thumbnail_key)
    await db.delete(item)
    await db.flush()
    await db.execute(
        update(MediaAsset)
        .where(MediaAsset.project_id == project.id, MediaAsset.position > deleted_position)
        .values(position=MediaAsset.position - 1)
    )
    await db.commit()
    return await list_media(project, db)


@router.put("/media/{media_id}", response_model=MediaResponse)
async def replace_media(
    media_id: uuid.UUID,
    request: Request,
    project: OwnedProject,
    db: Database,
    user: CurrentUser,
    x_filename: Annotated[str, Header(max_length=255)] = "media",
) -> MediaResponse:
    item = await db.scalar(
        select(MediaAsset).where(MediaAsset.id == media_id, MediaAsset.project_id == project.id)
    )
    if item is None:
        raise ApiError(404, "media_not_found", "رسانه پیدا نشد.")
    content_type = request.headers.get("content-type", "application/octet-stream").split(";", 1)[0]
    payload = await bounded_body(request)
    try:
        validated = validate_upload(x_filename, content_type, len(payload), payload[:32])
        probe = probe_bytes(payload, suffix_for_content_type(content_type))
    except (UploadRejected, subprocess.SubprocessError, ValueError, KeyError) as exc:
        if isinstance(exc, UploadRejected):
            raise ApiError(422, exc.code, exc.message_fa) from exc
        raise ApiError(422, "invalid_media", "این فایل رسانه‌ای قابل خواندن نیست.") from exc
    if validated.kind == "audio":
        raise ApiError(422, "visual_required", "در این بخش عکس یا کلیپ لازم است.")
    if validated.kind == "clip" and (probe.duration_ms <= 0 or probe.duration_ms > 60_000):
        raise ApiError(422, "clip_duration", "کلیپ باید حداکثر ۶۰ ثانیه باشد.")
    new_key = (
        f"users/{user.id}/projects/{project.id}/media/"
        f"{uuid.uuid4()}{suffix_for_content_type(content_type)}"
    )
    stored = storage().put_private(new_key, io.BytesIO(payload), content_type)
    old_key = item.object_key
    item.kind = validated.kind
    item.object_key = stored.key
    item.original_filename = validated.filename
    item.content_type = content_type
    item.size_bytes = stored.size
    item.width = probe.width
    item.height = probe.height
    item.duration_ms = probe.duration_ms if validated.kind == "clip" else None
    item.checksum_sha256 = stored.checksum_sha256
    await db.commit()
    storage().delete(old_key)
    return MediaResponse.model_validate(item).model_copy(
        update={"url": storage().presigned_get(item.object_key, 300)}
    )
