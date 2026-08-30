from __future__ import annotations

import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Project, User
from app.storage.base import ObjectStorage


async def delete_project(
    db: AsyncSession, storage: ObjectStorage, user_id: uuid.UUID, project_id: uuid.UUID
) -> bool:
    project = await db.scalar(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    if project is None:
        return False
    # Database deletion happens only after durable objects are gone. Repeating a
    # prefix delete is safe when a previous attempt stopped between these steps.
    storage.delete_prefix(f"users/{user_id}/projects/{project_id}/")
    await db.delete(project)
    await db.commit()
    return True


async def delete_account(db: AsyncSession, storage: ObjectStorage, user_id: uuid.UUID) -> bool:
    user = await db.scalar(select(User).where(User.id == user_id))
    if user is None:
        return False
    storage.delete_prefix(f"users/{user_id}/")
    await db.execute(delete(User).where(User.id == user_id))
    await db.commit()
    return True
