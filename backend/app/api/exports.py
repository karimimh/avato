from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Header
from pydantic import BaseModel
from sqlalchemy import select

from app.api.assets import storage
from app.api.dependencies import CurrentUser, Database, OwnedProject
from app.api.errors import ApiError
from app.db.models import AnalyticsEvent, ConsentRecord, Export, RenderJob
from app.services.credits import credit_balance
from app.workers.render_tasks import render_project_task

router = APIRouter(prefix="/projects/{project_id}", tags=["exports"])


class ExportRequest(BaseModel):
    tier: str
    owns_media: bool
    owns_voice: bool
    respects_privacy: bool
    no_impersonation: bool


class JobResponse(BaseModel):
    id: uuid.UUID
    status: str
    progress: int
    tier: str
    error_code: str | None
    error_detail: str | None


class DownloadResponse(BaseModel):
    url: str
    expires_seconds: int


class ExportItemResponse(BaseModel):
    id: uuid.UUID
    tier: str
    width: int
    height: int
    duration_ms: int
    watermarked: bool
    created_at: datetime


def job_response(job: RenderJob) -> JobResponse:
    return JobResponse(
        id=job.id,
        status=job.status,
        progress=job.progress,
        tier=job.kind,
        error_code=job.error_code,
        error_detail=job.error_detail,
    )


@router.post("/exports", response_model=JobResponse, status_code=202)
async def request_export(
    payload: ExportRequest,
    project: OwnedProject,
    db: Database,
    user: CurrentUser,
    idempotency_key: Annotated[str, Header(min_length=8, max_length=100)],
) -> JobResponse:
    if payload.tier not in {"free", "paid"}:
        raise ApiError(422, "invalid_export_tier", "نوع خروجی معتبر نیست.")
    if not all(
        [payload.owns_media, payload.owns_voice, payload.respects_privacy, payload.no_impersonation]
    ):
        raise ApiError(422, "rights_consent_required", "تأیید مالکیت و رضایت برای خروجی لازم است.")
    existing = await db.scalar(
        select(RenderJob).where(
            RenderJob.project_id == project.id, RenderJob.idempotency_key == idempotency_key
        )
    )
    if existing:
        return job_response(existing)
    if payload.tier == "free" and user.trial_used_at is not None:
        raise ApiError(409, "trial_already_used", "خروجی آزمایشی رایگان قبلاً استفاده شده است.")
    if payload.tier == "paid" and await credit_balance(db, user.id) < 1:
        reexport = await db.scalar(
            select(Export.id).where(
                Export.project_id == project.id,
                Export.tier == "paid",
                Export.reexport_until > datetime.now(UTC),
            )
        )
        if reexport is None:
            raise ApiError(402, "credit_required", "برای خروجی باکیفیت یک اعتبار لازم است.")
    now = datetime.now(UTC)
    for kind in ("media_rights", "voice_rights", "privacy", "no_impersonation"):
        db.add(
            ConsentRecord(
                user_id=user.id,
                project_id=project.id,
                kind=kind,
                policy_version="2026-08-30",
                accepted=True,
                accepted_at=now,
            )
        )
    revision_payload = {
        "project": str(project.id),
        "updated": project.updated_at.isoformat(),
        "tier": payload.tier,
    }
    job = RenderJob(
        project_id=project.id,
        kind=payload.tier,
        status="queued",
        idempotency_key=idempotency_key,
        progress=0,
        attempt_count=0,
        input_revision=hashlib.sha256(
            json.dumps(revision_payload, sort_keys=True).encode()
        ).hexdigest(),
    )
    db.add(job)
    project.status = "rendering"
    db.add(AnalyticsEvent(user_id=user.id, project_id=project.id, name="export_requested"))
    await db.commit()
    await db.refresh(job)
    render_project_task.apply_async(args=[str(job.id)], task_id=str(job.id))
    return job_response(job)


@router.get("/exports/{job_id}", response_model=JobResponse)
async def export_status(job_id: uuid.UUID, project: OwnedProject, db: Database) -> JobResponse:
    job = await db.scalar(
        select(RenderJob).where(RenderJob.id == job_id, RenderJob.project_id == project.id)
    )
    if job is None:
        raise ApiError(404, "render_job_not_found", "درخواست خروجی پیدا نشد.")
    return job_response(job)


@router.get("/exports", response_model=list[ExportItemResponse])
async def list_exports(project: OwnedProject, db: Database) -> list[ExportItemResponse]:
    items = list(
        (
            await db.scalars(
                select(Export)
                .where(Export.project_id == project.id)
                .order_by(Export.created_at.desc())
            )
        ).all()
    )
    return [
        ExportItemResponse(
            id=item.id,
            tier=item.tier,
            width=item.width,
            height=item.height,
            duration_ms=item.duration_ms,
            watermarked=item.watermarked,
            created_at=item.created_at,
        )
        for item in items
    ]


@router.post("/exports/{job_id}/cancel", response_model=JobResponse)
async def cancel_export(job_id: uuid.UUID, project: OwnedProject, db: Database) -> JobResponse:
    job = await db.scalar(
        select(RenderJob).where(RenderJob.id == job_id, RenderJob.project_id == project.id)
    )
    if job is None:
        raise ApiError(404, "render_job_not_found", "درخواست خروجی پیدا نشد.")
    if job.status not in {"queued", "running"}:
        raise ApiError(409, "cannot_cancel", "این پردازش دیگر قابل لغو نیست.")
    job.status = "cancelled"
    job.finished_at = datetime.now(UTC)
    await db.commit()
    return job_response(job)


@router.get("/exports/{export_id}/download", response_model=DownloadResponse)
async def download_export(
    export_id: uuid.UUID, project: OwnedProject, db: Database, user: CurrentUser
) -> DownloadResponse:
    item = await db.scalar(
        select(Export).where(Export.id == export_id, Export.project_id == project.id)
    )
    if item is None:
        raise ApiError(404, "export_not_found", "خروجی پیدا نشد.")
    db.add(AnalyticsEvent(user_id=user.id, project_id=project.id, name="export_downloaded"))
    await db.commit()
    return DownloadResponse(url=storage().presigned_get(item.object_key, 300), expires_seconds=300)


@router.post("/exports/{export_id}/share", response_model=DownloadResponse)
async def share_export(
    export_id: uuid.UUID, project: OwnedProject, db: Database, user: CurrentUser
) -> DownloadResponse:
    item = await db.scalar(
        select(Export).where(Export.id == export_id, Export.project_id == project.id)
    )
    if item is None:
        raise ApiError(404, "export_not_found", "خروجی پیدا نشد.")
    db.add(AnalyticsEvent(user_id=user.id, project_id=project.id, name="export_shared"))
    await db.commit()
    return DownloadResponse(url=storage().presigned_get(item.object_key, 300), expires_seconds=300)
