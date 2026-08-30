from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class ApiError(HTTPException):
    def __init__(
        self, status_code: int, code: str, message_fa: str, details: dict[str, Any] | None = None
    ) -> None:
        super().__init__(status_code=status_code, detail=message_fa)
        self.code = code
        self.message_fa = message_fa
        self.details = details or {}


async def api_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ApiError)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message_fa, "details": exc.details}},
    )
