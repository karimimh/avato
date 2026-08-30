from __future__ import annotations

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=200)
    display_name: str | None = Field(default=None, max_length=100)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
            raise ValueError("invalid email")
        return normalized


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    email: str
    display_name: str | None


class AuthResponse(BaseModel):
    token: str
    expires_at: datetime
    user: UserResponse


class ProjectCreate(BaseModel):
    duration_limit_seconds: int = 60
    title: str | None = Field(default=None, max_length=120)

    @field_validator("duration_limit_seconds")
    @classmethod
    def valid_duration(cls, value: int) -> int:
        if value not in {15, 30, 60}:
            raise ValueError("duration must be 15, 30, or 60 seconds")
        return value


class ProjectUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    secondary_line: str | None = Field(default=None, max_length=160)
    template_id: str | None = None
    music_track_id: str | None = None
    music_volume: str | None = None
    current_step: str | None = None
    cover_media_id: uuid.UUID | None = None

    @field_validator("template_id")
    @classmethod
    def valid_template(cls, value: str | None) -> str | None:
        if value is not None and value not in {"clean-story", "dynamic-voice", "memory-film"}:
            raise ValueError("unknown template")
        return value

    @field_validator("music_volume")
    @classmethod
    def valid_volume(cls, value: str | None) -> str | None:
        if value is not None and value not in {"low", "medium", "high"}:
            raise ValueError("unknown music volume")
        return value


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    status: str
    title: str | None
    secondary_line: str | None
    duration_limit_seconds: int
    template_id: str
    music_track_id: str | None
    music_volume: str
    cover_media_id: uuid.UUID | None
    current_step: str
    last_activity_at: datetime
    expires_at: datetime
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]


class DeleteResponse(BaseModel):
    deleted: bool
