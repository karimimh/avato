"""store mixin timestamps with UTC timezone

Revision ID: 20260830_0002
Revises: 20260830_0001
Create Date: 2026-08-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260830_0002"
down_revision: str | None = "20260830_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = (
    "users",
    "sessions",
    "templates",
    "music_tracks",
    "projects",
    "audio_assets",
    "media_assets",
    "transcript_segments",
    "transcript_words",
    "media_assignments",
    "render_jobs",
    "exports",
    "purchases",
    "idempotency_records",
)


def upgrade() -> None:
    for table in TABLES:
        for column in ("created_at", "updated_at"):
            op.alter_column(
                table,
                column,
                type_=sa.DateTime(timezone=True),
                postgresql_using=f"{column} AT TIME ZONE 'UTC'",
            )


def downgrade() -> None:
    for table in reversed(TABLES):
        for column in ("updated_at", "created_at"):
            op.alter_column(
                table,
                column,
                type_=sa.DateTime(timezone=False),
                postgresql_using=f"{column} AT TIME ZONE 'UTC'",
            )
