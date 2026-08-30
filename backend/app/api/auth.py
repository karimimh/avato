from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter
from sqlalchemy import select

from app.api.assets import storage
from app.api.dependencies import CurrentUser, Database
from app.api.errors import ApiError
from app.api.schemas import AuthResponse, DeleteResponse, LoginRequest, UserCreate, UserResponse
from app.core.security import hash_password, new_session_token, verify_password
from app.db.models import Session, User
from app.services.deletion import delete_account

router = APIRouter(prefix="/auth", tags=["authentication"])
SESSION_DAYS = 30


def _new_session(user: User) -> tuple[Session, str]:
    now = datetime.now(UTC)
    token = new_session_token()
    session = Session(
        user_id=user.id,
        token_hash=token.digest,
        expires_at=now + timedelta(days=SESSION_DAYS),
        last_seen_at=now,
    )
    return session, token.plaintext


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(payload: UserCreate, db: Database) -> AuthResponse:
    if await db.scalar(select(User.id).where(User.email == payload.email)) is not None:
        raise ApiError(409, "email_exists", "برای این ایمیل قبلاً حساب ساخته شده است.")
    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
    )
    db.add(user)
    await db.flush()
    session, token = _new_session(user)
    db.add(session)
    await db.commit()
    await db.refresh(user)
    return AuthResponse(
        token=token, expires_at=session.expires_at, user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, db: Database) -> AuthResponse:
    user = await db.scalar(select(User).where(User.email == payload.email.strip().lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise ApiError(401, "invalid_credentials", "ایمیل یا رمز عبور درست نیست.")
    session, token = _new_session(user)
    db.add(session)
    await db.commit()
    return AuthResponse(
        token=token, expires_at=session.expires_at, user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
async def me(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)


@router.delete("/account", response_model=DeleteResponse)
async def remove_account(user: CurrentUser, db: Database) -> DeleteResponse:
    deleted = await delete_account(db, storage(), user.id)
    return DeleteResponse(deleted=deleted)
