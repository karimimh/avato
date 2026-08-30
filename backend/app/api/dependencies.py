from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated, cast

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ApiError
from app.core.security import digest_session_token
from app.db.models import Project, Session, User
from app.db.session import get_db_session

Database = Annotated[AsyncSession, Depends(get_db_session)]


async def current_user(db: Database, authorization: Annotated[str | None, Header()] = None) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise ApiError(401, "authentication_required", "برای ادامه وارد حساب خود شوید.")
    token = authorization.removeprefix("Bearer ").strip()
    statement = (
        select(User, Session)
        .join(Session, Session.user_id == User.id)
        .where(
            Session.token_hash == digest_session_token(token),
            Session.revoked_at.is_(None),
            Session.expires_at > datetime.now(UTC),
            User.deleted_at.is_(None),
            User.is_active.is_(True),
        )
    )
    result = (await db.execute(statement)).first()
    if result is None:
        raise ApiError(401, "invalid_session", "نشست شما معتبر نیست؛ دوباره وارد شوید.")
    user = cast(User, result[0])
    session = cast(Session, result[1])
    session.last_seen_at = datetime.now(UTC)
    return user


CurrentUser = Annotated[User, Depends(current_user)]


async def owned_project(project_id: uuid.UUID, db: Database, user: CurrentUser) -> Project:
    project = await db.scalar(
        select(Project).where(Project.id == project_id, Project.user_id == user.id)
    )
    if project is None:
        # Deliberately do not reveal whether another user's project exists.
        raise ApiError(404, "project_not_found", "پروژه پیدا نشد.")
    return project


OwnedProject = Annotated[Project, Depends(owned_project)]
