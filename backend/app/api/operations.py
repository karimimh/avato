from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, text

from app.api.dependencies import CurrentUser, Database
from app.db.models import AnalyticsEvent, Project

router = APIRouter(tags=["operations"])

EVENT_NAMES = {
    "project_started",
    "voice_added",
    "preview_reached",
    "transcript_corrected",
    "template_changed",
    "media_assignment_replaced",
    "export_requested",
    "export_succeeded",
    "export_failed",
    "export_downloaded",
    "export_shared",
    "purchase_started",
    "purchase_succeeded",
    "second_project_created",
    "draft_rated",
}
ALLOWED_PROPERTY_KEYS = {
    "duration_bucket",
    "template_id",
    "media_count",
    "corrected_word_count",
    "tier",
    "rating",
    "saved_time_bucket",
    "referral",
}


class AnalyticsRequest(BaseModel):
    name: str
    project_id: str | None = None
    properties: dict[str, str | int | bool] = Field(default_factory=dict)

    @field_validator("name")
    @classmethod
    def valid_name(cls, value: str) -> str:
        if value not in EVENT_NAMES:
            raise ValueError("unknown analytics event")
        return value

    @field_validator("properties")
    @classmethod
    def safe_properties(cls, value: dict[str, str | int | bool]) -> dict[str, str | int | bool]:
        if set(value) - ALLOWED_PROPERTY_KEYS:
            raise ValueError("analytics properties may not contain private content")
        return value


@router.get("/ready")
async def readiness(db: Database) -> dict[str, str]:
    await db.execute(text("SELECT 1"))
    return {"status": "ready", "checked_at": datetime.now(UTC).isoformat()}


@router.post("/analytics", status_code=202)
async def record_analytics(
    payload: AnalyticsRequest, db: Database, user: CurrentUser
) -> dict[str, bool]:
    project_uuid = None
    if payload.project_id:
        project_uuid = uuid.UUID(payload.project_id)
        owned = await db.scalar(
            select(Project.id).where(Project.id == project_uuid, Project.user_id == user.id)
        )
        if owned is None:
            project_uuid = None
    db.add(
        AnalyticsEvent(
            user_id=user.id,
            project_id=project_uuid,
            name=payload.name,
            properties=payload.properties,
        )
    )
    await db.commit()
    return {"accepted": True}
