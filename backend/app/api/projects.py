from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter
from sqlalchemy import select

from app.api.assets import storage
from app.api.dependencies import CurrentUser, Database, OwnedProject
from app.api.errors import ApiError
from app.api.schemas import (
    DeleteResponse,
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.db.models import MediaAsset, Project
from app.domain.projects import activity_expiry
from app.services.deletion import delete_project as delete_project_data

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=201)
async def create_project(payload: ProjectCreate, db: Database, user: CurrentUser) -> Project:
    now = datetime.now(UTC)
    project = Project(
        user_id=user.id,
        title=payload.title,
        duration_limit_seconds=payload.duration_limit_seconds,
        template_id="clean-story",
        last_activity_at=now,
        expires_at=activity_expiry(now),
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@router.get("", response_model=ProjectListResponse)
async def list_projects(db: Database, user: CurrentUser) -> ProjectListResponse:
    projects = list(
        (
            await db.scalars(
                select(Project)
                .where(Project.user_id == user.id)
                .order_by(Project.last_activity_at.desc())
                .limit(50)
            )
        ).all()
    )
    return ProjectListResponse(items=[ProjectResponse.model_validate(item) for item in projects])


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project: OwnedProject) -> Project:
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(payload: ProjectUpdate, project: OwnedProject, db: Database) -> Project:
    updates: dict[str, Any] = payload.model_dump(exclude_unset=True)
    cover_media_id = updates.get("cover_media_id")
    if cover_media_id is not None:
        cover = await db.scalar(
            select(MediaAsset).where(
                MediaAsset.id == cover_media_id,
                MediaAsset.project_id == project.id,
            )
        )
        if cover is None:
            raise ApiError(422, "invalid_cover", "تصویر جلد باید از رسانه‌های همین پروژه باشد.")
    for field, value in updates.items():
        setattr(project, field, value)
    now = datetime.now(UTC)
    project.last_activity_at = now
    project.expires_at = activity_expiry(now)
    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", response_model=DeleteResponse)
async def remove_project(project: OwnedProject, db: Database) -> DeleteResponse:
    deleted = await delete_project_data(db, storage(), project.user_id, project.id)
    return DeleteResponse(deleted=deleted)
