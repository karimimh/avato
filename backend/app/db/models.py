from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, utcnow


def new_uuid() -> uuid.UUID:
    return uuid.uuid4()


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    display_name: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    trial_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    sessions: Mapped[list[Session]] = relationship(cascade="all, delete-orphan")
    projects: Mapped[list[Project]] = relationship(cascade="all, delete-orphan")


class Session(TimestampMixin, Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[bytes] = mapped_column(LargeBinary(32), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    user_agent: Mapped[str | None] = mapped_column(String(300))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Template(TimestampMixin, Base):
    __tablename__ = "templates"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name_fa: Mapped[str] = mapped_column(String(100))
    description_fa: Mapped[str] = mapped_column(String(500))
    render_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class MusicTrack(TimestampMixin, Base):
    __tablename__ = "music_tracks"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    name_fa: Mapped[str] = mapped_column(String(100))
    mood: Mapped[str] = mapped_column(String(30))
    object_key: Mapped[str] = mapped_column(String(1000))
    duration_ms: Mapped[int] = mapped_column(Integer)
    license_name: Mapped[str] = mapped_column(String(200))
    license_url: Mapped[str | None] = mapped_column(String(1000))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Project(TimestampMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (
        CheckConstraint("duration_limit_seconds IN (15, 30, 60)", name="valid_duration_limit"),
        Index("ix_projects_owner_activity", "user_id", "last_activity_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(30), default="draft", index=True)
    title: Mapped[str | None] = mapped_column(String(120))
    secondary_line: Mapped[str | None] = mapped_column(String(160))
    duration_limit_seconds: Mapped[int] = mapped_column(Integer, default=60)
    template_id: Mapped[str] = mapped_column(
        ForeignKey("templates.id", ondelete="RESTRICT"), default="clean-story"
    )
    music_track_id: Mapped[str | None] = mapped_column(
        ForeignKey("music_tracks.id", ondelete="SET NULL")
    )
    music_volume: Mapped[str] = mapped_column(String(20), default="low")
    cover_media_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    current_step: Mapped[str] = mapped_column(String(30), default="voice")
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    expiry_warned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    audio_assets: Mapped[list[AudioAsset]] = relationship(cascade="all, delete-orphan")
    media_assets: Mapped[list[MediaAsset]] = relationship(
        cascade="all, delete-orphan", order_by="MediaAsset.position"
    )
    transcript_segments: Mapped[list[TranscriptSegment]] = relationship(
        cascade="all, delete-orphan", order_by="TranscriptSegment.position"
    )
    render_jobs: Mapped[list[RenderJob]] = relationship(cascade="all, delete-orphan")
    exports: Mapped[list[Export]] = relationship(cascade="all, delete-orphan")


class AudioAsset(TimestampMixin, Base):
    __tablename__ = "audio_assets"
    __table_args__ = (UniqueConstraint("project_id", "kind"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(20))
    object_key: Mapped[str] = mapped_column(String(1000), unique=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    duration_ms: Mapped[int] = mapped_column(Integer)
    trim_start_ms: Mapped[int] = mapped_column(Integer, default=0)
    trim_end_ms: Mapped[int | None] = mapped_column(Integer)
    analysis: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    checksum_sha256: Mapped[str] = mapped_column(String(64))


class MediaAsset(TimestampMixin, Base):
    __tablename__ = "media_assets"
    __table_args__ = (
        UniqueConstraint("project_id", "position"),
        CheckConstraint("position >= 0 AND position < 12", name="valid_position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(20))
    position: Mapped[int] = mapped_column(Integer)
    object_key: Mapped[str] = mapped_column(String(1000), unique=True)
    thumbnail_key: Mapped[str | None] = mapped_column(String(1000))
    original_filename: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    checksum_sha256: Mapped[str] = mapped_column(String(64))


class TranscriptSegment(TimestampMixin, Base):
    __tablename__ = "transcript_segments"
    __table_args__ = (
        UniqueConstraint("project_id", "position"),
        CheckConstraint("start_ms >= 0 AND end_ms > start_ms", name="valid_timing"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    start_ms: Mapped[int] = mapped_column(Integer)
    end_ms: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    original_text: Mapped[str] = mapped_column(Text)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4))
    words: Mapped[list[TranscriptWord]] = relationship(
        cascade="all, delete-orphan", order_by="TranscriptWord.position"
    )
    assignment: Mapped[MediaAssignment | None] = relationship(cascade="all, delete-orphan")


class TranscriptWord(TimestampMixin, Base):
    __tablename__ = "transcript_words"
    __table_args__ = (UniqueConstraint("segment_id", "position"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    segment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("transcript_segments.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    start_ms: Mapped[int] = mapped_column(Integer)
    end_ms: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(String(200))
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 4))


class MediaAssignment(TimestampMixin, Base):
    __tablename__ = "media_assignments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    segment_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("transcript_segments.id", ondelete="CASCADE"), unique=True
    )
    media_asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("media_assets.id", ondelete="CASCADE"), index=True
    )
    source: Mapped[str] = mapped_column(String(20), default="automatic")
    clip_offset_ms: Mapped[int] = mapped_column(Integer, default=0)


class RenderJob(TimestampMixin, Base):
    __tablename__ = "render_jobs"
    __table_args__ = (UniqueConstraint("project_id", "idempotency_key"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)
    idempotency_key: Mapped[str] = mapped_column(String(100))
    progress: Mapped[int] = mapped_column(Integer, default=0)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    input_revision: Mapped[str] = mapped_column(String(64))
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_detail: Mapped[str | None] = mapped_column(String(1000))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Export(TimestampMixin, Base):
    __tablename__ = "exports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    render_job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("render_jobs.id", ondelete="RESTRICT"), unique=True
    )
    tier: Mapped[str] = mapped_column(String(20))
    object_key: Mapped[str] = mapped_column(String(1000), unique=True)
    cover_object_key: Mapped[str] = mapped_column(String(1000), unique=True)
    width: Mapped[int] = mapped_column(Integer)
    height: Mapped[int] = mapped_column(Integer)
    duration_ms: Mapped[int] = mapped_column(Integer)
    size_bytes: Mapped[int] = mapped_column(Integer)
    watermarked: Mapped[bool] = mapped_column(Boolean)
    checksum_sha256: Mapped[str] = mapped_column(String(64))
    reexport_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CreditLedgerEntry(Base):
    __tablename__ = "credit_ledger_entries"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key"),
        CheckConstraint("amount != 0", name="nonzero_amount"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    amount: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(30))
    reference_type: Mapped[str] = mapped_column(String(30))
    reference_id: Mapped[str] = mapped_column(String(100))
    idempotency_key: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Purchase(TimestampMixin, Base):
    __tablename__ = "purchases"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(40))
    provider_reference: Mapped[str | None] = mapped_column(String(200), unique=True)
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True)
    status: Mapped[str] = mapped_column(String(30), default="initiated")
    amount_rials: Mapped[int] = mapped_column(Integer)
    credits: Mapped[int] = mapped_column(Integer)
    callback_payload_digest: Mapped[str | None] = mapped_column(String(64))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(50))
    policy_version: Mapped[str] = mapped_column(String(30))
    accepted: Mapped[bool] = mapped_column(Boolean)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ip_digest: Mapped[str | None] = mapped_column(String(64))


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"
    __table_args__ = (Index("ix_analytics_name_created", "name", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL"), index=True
    )
    name: Mapped[str] = mapped_column(String(80))
    properties: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class IdempotencyRecord(TimestampMixin, Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (UniqueConstraint("scope", "key"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=new_uuid)
    scope: Mapped[str] = mapped_column(String(100))
    key: Mapped[str] = mapped_column(String(100))
    request_digest: Mapped[str] = mapped_column(String(64))
    status_code: Mapped[int | None] = mapped_column(Integer)
    response_body: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
