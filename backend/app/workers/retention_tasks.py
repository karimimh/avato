from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta

from celery import Task
from sqlalchemy import select

from app.db.models import AnalyticsEvent, Project
from app.db.session import async_session_factory, engine
from app.storage.s3 import S3ObjectStorage
from app.workers.celery_app import celery_app


@celery_app.task(name="avato.warn_expiring_projects", bind=True)  # type: ignore[untyped-decorator]
def warn_expiring_projects_task(self: Task) -> dict[str, int]:
    del self
    return asyncio.run(_warn_expiring_projects_isolated())


async def _warn_expiring_projects_isolated() -> dict[str, int]:
    try:
        return await _warn_expiring_projects()
    finally:
        await engine.dispose()


async def _warn_expiring_projects() -> dict[str, int]:
    now = datetime.now(UTC)
    async with async_session_factory() as db:
        projects = list(
            (
                await db.scalars(
                    select(Project).where(
                        Project.expires_at > now,
                        Project.expires_at <= now + timedelta(days=3),
                        Project.expiry_warned_at.is_(None),
                    )
                )
            ).all()
        )
        for project in projects:
            project.expiry_warned_at = now
            db.add(
                AnalyticsEvent(
                    user_id=project.user_id,
                    project_id=project.id,
                    name="expiry_warning_due",
                    properties={"days": max(0, (project.expires_at - now).days)},
                )
            )
        await db.commit()
        return {"warned": len(projects)}


@celery_app.task(name="avato.delete_expired_projects", bind=True)  # type: ignore[untyped-decorator]
def delete_expired_projects_task(self: Task) -> dict[str, int]:
    del self
    return asyncio.run(_delete_expired_projects_isolated())


async def _delete_expired_projects_isolated() -> dict[str, int]:
    try:
        return await _delete_expired_projects()
    finally:
        await engine.dispose()


async def _delete_expired_projects() -> dict[str, int]:
    now = datetime.now(UTC)
    storage = S3ObjectStorage()
    async with async_session_factory() as db:
        projects = list((await db.scalars(select(Project).where(Project.expires_at <= now))).all())
        for project in projects:
            storage.delete_prefix(f"users/{project.user_id}/projects/{project.id}/")
            await db.delete(project)
        await db.commit()
        return {"deleted": len(projects)}
