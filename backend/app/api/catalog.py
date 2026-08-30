from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from app.api.dependencies import Database
from app.db.models import MusicTrack, Template

router = APIRouter(prefix="/catalog", tags=["catalog"])


class TemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name_fa: str
    description_fa: str


class MusicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name_fa: str
    mood: str
    duration_ms: int
    license_name: str


class CatalogResponse(BaseModel):
    templates: list[TemplateResponse]
    music: list[MusicResponse]


@router.get("", response_model=CatalogResponse)
async def catalog(db: Database) -> CatalogResponse:
    templates = list((await db.scalars(select(Template).where(Template.is_active.is_(True)))).all())
    music = list((await db.scalars(select(MusicTrack).where(MusicTrack.is_active.is_(True)))).all())
    return CatalogResponse(
        templates=[TemplateResponse.model_validate(item) for item in templates],
        music=[MusicResponse.model_validate(item) for item in music],
    )
