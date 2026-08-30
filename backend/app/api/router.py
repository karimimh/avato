from fastapi import APIRouter

from app.api.assets import router as assets_router
from app.api.auth import router as auth_router
from app.api.catalog import router as catalog_router
from app.api.draft import router as draft_router
from app.api.exports import router as exports_router
from app.api.operations import router as operations_router
from app.api.payments import router as payments_router
from app.api.projects import router as projects_router
from app.api.transcript import router as transcript_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(assets_router)
api_router.include_router(transcript_router)
api_router.include_router(draft_router)
api_router.include_router(catalog_router)
api_router.include_router(payments_router)
api_router.include_router(exports_router)
api_router.include_router(operations_router)


@api_router.get("/health", tags=["infrastructure"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
