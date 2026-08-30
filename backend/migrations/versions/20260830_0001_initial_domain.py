"""initial Avato domain

Revision ID: 20260830_0001
Revises:
Create Date: 2026-08-30
"""

from collections.abc import Sequence

from alembic import op

from app.db.base import Base
from app.db.models import MusicTrack, Template

revision: str = "20260830_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # This reviewed initial migration intentionally mirrors the complete initial
    # metadata. Subsequent revisions must use explicit incremental operations.
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)
    op.bulk_insert(
        Template.__table__,
        [
            {
                "id": "clean-story",
                "name_fa": "روایت ساده",
                "description_fa": "تمیز و خوانا برای نظرها و آموزش‌های کوتاه",
                "render_config": {"motion": "slow-zoom", "transition": "cut"},
                "is_active": True,
            },
            {
                "id": "dynamic-voice",
                "name_fa": "صدای پویا",
                "description_fa": "پرانرژی با زیرنویس درشت و موج صدا",
                "render_config": {"motion": "pulse", "transition": "fast-fade"},
                "is_active": True,
            },
            {
                "id": "memory-film",
                "name_fa": "فیلم خاطره",
                "description_fa": "آرام و احساسی برای آدم‌ها، سفرها و مناسبت‌ها",
                "render_config": {"motion": "ken-burns", "transition": "crossfade"},
                "is_active": True,
            },
        ],
    )
    op.bulk_insert(
        MusicTrack.__table__,
        [
            {
                "id": "calm-local",
                "name_fa": "آرام",
                "mood": "calm",
                "object_key": "catalog/music/calm-local.wav",
                "duration_ms": 60000,
                "license_name": "Avato generated test fixture / CC0",
                "license_url": None,
                "is_active": True,
            },
            {
                "id": "emotional-local",
                "name_fa": "احساسی",
                "mood": "emotional",
                "object_key": "catalog/music/emotional-local.wav",
                "duration_ms": 60000,
                "license_name": "Avato generated test fixture / CC0",
                "license_url": None,
                "is_active": True,
            },
            {
                "id": "upbeat-local",
                "name_fa": "پرانرژی",
                "mood": "upbeat",
                "object_key": "catalog/music/upbeat-local.wav",
                "duration_ms": 60000,
                "license_name": "Avato generated test fixture / CC0",
                "license_url": None,
                "is_active": True,
            },
        ],
    )


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind(), checkfirst=True)
