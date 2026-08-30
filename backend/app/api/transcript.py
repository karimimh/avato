from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, select, update
from sqlalchemy.orm import selectinload

from app.api.dependencies import Database, OwnedProject
from app.api.errors import ApiError
from app.db.models import TranscriptSegment, TranscriptWord
from app.domain.transcript import Segment, merge_segments, split_segment

router = APIRouter(prefix="/projects/{project_id}/transcript", tags=["transcript"])


class WordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    position: int
    start_ms: int
    end_ms: int
    text: str
    confidence: Decimal


class SegmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    position: int
    start_ms: int
    end_ms: int
    text: str
    original_text: str
    confidence: Decimal
    words: list[WordResponse]


class TranscriptResponse(BaseModel):
    segments: list[SegmentResponse]


class EditSegmentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)


class SplitSegmentRequest(BaseModel):
    character_index: int = Field(gt=0)


class MergeSegmentRequest(BaseModel):
    next_segment_id: uuid.UUID


def as_domain(record: TranscriptSegment) -> Segment:
    return Segment(
        id=str(record.id),
        position=record.position,
        start_ms=record.start_ms,
        end_ms=record.end_ms,
        text=record.text,
        original_text=record.original_text,
        confidence=float(record.confidence),
    )


async def segment_for_project(
    db: Database, project_id: uuid.UUID, segment_id: uuid.UUID
) -> TranscriptSegment:
    segment = await db.scalar(
        select(TranscriptSegment)
        .options(selectinload(TranscriptSegment.words))
        .where(TranscriptSegment.id == segment_id, TranscriptSegment.project_id == project_id)
    )
    if segment is None:
        raise ApiError(404, "segment_not_found", "بخش زیرنویس پیدا نشد.")
    return segment


@router.get("", response_model=TranscriptResponse)
async def get_transcript(project: OwnedProject, db: Database) -> TranscriptResponse:
    segments = list(
        (
            await db.scalars(
                select(TranscriptSegment)
                .options(selectinload(TranscriptSegment.words))
                .where(TranscriptSegment.project_id == project.id)
                .order_by(TranscriptSegment.position)
            )
        ).all()
    )
    return TranscriptResponse(
        segments=[SegmentResponse.model_validate(segment) for segment in segments]
    )


@router.patch("/segments/{segment_id}", response_model=SegmentResponse)
async def edit_transcript_segment(
    segment_id: uuid.UUID,
    payload: EditSegmentRequest,
    project: OwnedProject,
    db: Database,
) -> SegmentResponse:
    segment = await segment_for_project(db, project.id, segment_id)
    segment.text = " ".join(payload.text.split())
    await db.commit()
    return SegmentResponse.model_validate(segment)


@router.post("/segments/{segment_id}/split", response_model=TranscriptResponse)
async def split_transcript_segment(
    segment_id: uuid.UUID,
    payload: SplitSegmentRequest,
    project: OwnedProject,
    db: Database,
) -> TranscriptResponse:
    segment = await segment_for_project(db, project.id, segment_id)
    try:
        first, second = split_segment(as_domain(segment), payload.character_index)
    except ValueError as exc:
        raise ApiError(422, "invalid_split", "محل جداکردن زیرنویس معتبر نیست.") from exc
    await db.execute(
        update(TranscriptSegment)
        .where(
            TranscriptSegment.project_id == project.id,
            TranscriptSegment.position > segment.position,
        )
        .values(position=TranscriptSegment.position + 1000)
    )
    await db.execute(
        update(TranscriptSegment)
        .where(
            TranscriptSegment.project_id == project.id,
            TranscriptSegment.position > 1000,
        )
        .values(position=TranscriptSegment.position - 999)
    )
    segment.end_ms = first.end_ms
    segment.text = first.text
    segment.original_text = first.original_text
    await db.execute(delete(TranscriptWord).where(TranscriptWord.segment_id == segment.id))
    db.add(
        TranscriptSegment(
            project_id=project.id,
            position=second.position,
            start_ms=second.start_ms,
            end_ms=second.end_ms,
            text=second.text,
            original_text=second.original_text,
            confidence=segment.confidence,
        )
    )
    await db.commit()
    return await get_transcript(project, db)


@router.post("/segments/{segment_id}/merge", response_model=TranscriptResponse)
async def merge_transcript_segment(
    segment_id: uuid.UUID,
    payload: MergeSegmentRequest,
    project: OwnedProject,
    db: Database,
) -> TranscriptResponse:
    first = await segment_for_project(db, project.id, segment_id)
    second = await segment_for_project(db, project.id, payload.next_segment_id)
    try:
        merged = merge_segments(as_domain(first), as_domain(second))
    except ValueError as exc:
        raise ApiError(422, "invalid_merge", "فقط دو بخش کنار هم قابل ادغام‌اند.") from exc
    first.end_ms = merged.end_ms
    first.text = merged.text
    first.original_text = merged.original_text
    first.confidence = Decimal(str(merged.confidence))
    await db.delete(second)
    await db.flush()
    await db.execute(
        update(TranscriptSegment)
        .where(
            TranscriptSegment.project_id == project.id,
            TranscriptSegment.position > second.position,
        )
        .values(position=TranscriptSegment.position - 1)
    )
    await db.commit()
    return await get_transcript(project, db)


@router.post("/restore", response_model=TranscriptResponse)
async def restore_transcript(project: OwnedProject, db: Database) -> TranscriptResponse:
    await db.execute(
        update(TranscriptSegment)
        .where(TranscriptSegment.project_id == project.id)
        .values(text=TranscriptSegment.original_text)
    )
    await db.commit()
    return await get_transcript(project, db)
