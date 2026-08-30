from __future__ import annotations

import uuid

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import delete, select

from app.api.dependencies import Database, OwnedProject
from app.api.errors import ApiError
from app.db.models import MediaAsset, MediaAssignment, TranscriptSegment
from app.domain.draft import SpeechBoundary, automatic_sections, media_count_state

router = APIRouter(prefix="/projects/{project_id}/draft", tags=["draft"])


class AssignmentResponse(BaseModel):
    segment_id: uuid.UUID
    media_id: uuid.UUID
    source: str
    reused: bool


class DraftResponse(BaseModel):
    assignments: list[AssignmentResponse]
    media_guidance: str


class AssignmentUpdate(BaseModel):
    media_id: uuid.UUID


@router.get("", response_model=DraftResponse)
async def get_draft(project: OwnedProject, db: Database) -> DraftResponse:
    segments = list(
        (
            await db.scalars(
                select(TranscriptSegment)
                .where(TranscriptSegment.project_id == project.id)
                .order_by(TranscriptSegment.position)
            )
        ).all()
    )
    media_count = len(
        (await db.scalars(select(MediaAsset.id).where(MediaAsset.project_id == project.id))).all()
    )
    assignments: list[AssignmentResponse] = []
    seen_media: set[uuid.UUID] = set()
    for segment in segments:
        assignment = await db.scalar(
            select(MediaAssignment).where(MediaAssignment.segment_id == segment.id)
        )
        if assignment:
            assignments.append(
                AssignmentResponse(
                    segment_id=segment.id,
                    media_id=assignment.media_asset_id,
                    source=assignment.source,
                    reused=assignment.media_asset_id in seen_media,
                )
            )
            seen_media.add(assignment.media_asset_id)
    duration_seconds = segments[-1].end_ms / 1000 if segments else 0
    return DraftResponse(
        assignments=assignments,
        media_guidance=media_count_state(media_count, duration_seconds),
    )


@router.post("", response_model=DraftResponse)
async def generate_draft(project: OwnedProject, db: Database) -> DraftResponse:
    segments = list(
        (
            await db.scalars(
                select(TranscriptSegment)
                .where(TranscriptSegment.project_id == project.id)
                .order_by(TranscriptSegment.position)
            )
        ).all()
    )
    media = list(
        (
            await db.scalars(
                select(MediaAsset)
                .where(MediaAsset.project_id == project.id)
                .order_by(MediaAsset.position)
            )
        ).all()
    )
    if not segments:
        raise ApiError(409, "transcript_required", "ابتدا پردازش و بازبینی زیرنویس را کامل کنید.")
    if not media:
        raise ApiError(409, "media_required", "حداقل یک عکس یا کلیپ لازم است.")
    sections = automatic_sections(
        [SpeechBoundary(item.start_ms, item.end_ms) for item in segments],
        [str(item.id) for item in media],
        segments[-1].end_ms,
    )
    await db.execute(
        delete(MediaAssignment).where(
            MediaAssignment.segment_id.in_([segment.id for segment in segments])
        )
    )
    response: list[AssignmentResponse] = []
    for segment, section in zip(segments, sections, strict=True):
        assignment = MediaAssignment(
            segment_id=segment.id,
            media_asset_id=uuid.UUID(section.media_id),
            source="automatic",
            clip_offset_ms=0,
        )
        db.add(assignment)
        response.append(
            AssignmentResponse(
                segment_id=segment.id,
                media_id=assignment.media_asset_id,
                source="automatic",
                reused=section.reused,
            )
        )
    project.current_step = "preview"
    await db.commit()
    duration_seconds = segments[-1].end_ms / 1000
    return DraftResponse(
        assignments=response,
        media_guidance=media_count_state(len(media), duration_seconds),
    )


@router.patch("/segments/{segment_id}", response_model=AssignmentResponse)
async def change_assignment(
    segment_id: uuid.UUID,
    payload: AssignmentUpdate,
    project: OwnedProject,
    db: Database,
) -> AssignmentResponse:
    segment = await db.scalar(
        select(TranscriptSegment).where(
            TranscriptSegment.id == segment_id, TranscriptSegment.project_id == project.id
        )
    )
    media = await db.scalar(
        select(MediaAsset).where(
            MediaAsset.id == payload.media_id, MediaAsset.project_id == project.id
        )
    )
    if segment is None or media is None:
        raise ApiError(404, "assignment_resource_missing", "بخش یا رسانه پیدا نشد.")
    assignment = await db.scalar(
        select(MediaAssignment).where(MediaAssignment.segment_id == segment.id)
    )
    if assignment is None:
        assignment = MediaAssignment(
            segment_id=segment.id,
            media_asset_id=media.id,
            source="manual",
            clip_offset_ms=0,
        )
        db.add(assignment)
    else:
        assignment.media_asset_id = media.id
        assignment.source = "manual"
    await db.commit()
    return AssignmentResponse(
        segment_id=segment.id, media_id=media.id, source="manual", reused=False
    )
