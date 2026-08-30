# The local checkout HTML is an intentionally compact self-contained fixture.
# ruff: noqa: E501

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from functools import lru_cache
from typing import Annotated, TypedDict

from fastapi import APIRouter, Header, Query, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import select

from app.api.dependencies import CurrentUser, Database
from app.api.errors import ApiError
from app.core.config import settings
from app.db.models import Purchase
from app.payments.base import PaymentProvider
from app.payments.local import LocalPaymentProvider
from app.payments.zarinpal import ZarinpalPaymentProvider
from app.services.credits import credit_balance, grant_purchase

router = APIRouter(prefix="/payments", tags=["payments"])


class CreditPack(TypedDict):
    credits: int
    amount_rials: int
    name_fa: str


CREDIT_PACKS: dict[str, CreditPack] = {
    "small": {"credits": 1, "amount_rials": 490_000, "name_fa": "یک خروجی"},
    "medium": {"credits": 5, "amount_rials": 1_990_000, "name_fa": "پنج خروجی"},
    "large": {"credits": 12, "amount_rials": 3_990_000, "name_fa": "دوازده خروجی"},
    "monthly": {"credits": 8, "amount_rials": 2_790_000, "name_fa": "سهمیهٔ ماهانه"},
}


class PackResponse(BaseModel):
    id: str
    credits: int
    amount_rials: int
    name_fa: str


class PacksResponse(BaseModel):
    items: list[PackResponse]


class PurchaseRequest(BaseModel):
    pack_id: str


class PurchaseResponse(BaseModel):
    purchase_id: uuid.UUID
    payment_url: str
    status: str


class CallbackResponse(BaseModel):
    status: str
    balance: int | None = None
    reference_id: str | None = None


@lru_cache
def payment_provider() -> PaymentProvider:
    if settings.payment_provider == "zarinpal":
        return ZarinpalPaymentProvider(
            settings.zarinpal_merchant_id, sandbox=settings.zarinpal_sandbox
        )
    return LocalPaymentProvider(settings.payment_local_secret)


def payment_url_for(authority: str) -> str:
    if settings.payment_provider == "zarinpal":
        host = (
            "https://sandbox.zarinpal.com"
            if settings.zarinpal_sandbox
            else "https://payment.zarinpal.com"
        )
        return f"{host}/pg/StartPay/{authority}"
    return f"http://localhost:8080/api/payments/local/checkout?authority={authority}"


@router.get("/packs", response_model=PacksResponse)
async def packs() -> PacksResponse:
    return PacksResponse(
        items=[PackResponse(id=key, **value) for key, value in CREDIT_PACKS.items()]
    )


@router.post("/purchases", response_model=PurchaseResponse, status_code=201)
async def initiate_purchase(
    payload: PurchaseRequest,
    db: Database,
    user: CurrentUser,
    idempotency_key: Annotated[str, Header(min_length=8, max_length=100)],
) -> PurchaseResponse:
    pack = CREDIT_PACKS.get(payload.pack_id)
    if pack is None:
        raise ApiError(422, "unknown_credit_pack", "بستهٔ اعتبار معتبر نیست.")
    existing = await db.scalar(
        select(Purchase).where(
            Purchase.user_id == user.id, Purchase.idempotency_key == idempotency_key
        )
    )
    if existing and existing.provider_reference:
        return PurchaseResponse(
            purchase_id=existing.id,
            payment_url=payment_url_for(existing.provider_reference),
            status=existing.status,
        )
    purchase = existing or Purchase(
        user_id=user.id,
        provider=settings.payment_provider,
        idempotency_key=idempotency_key,
        status="initiated",
        amount_rials=int(pack["amount_rials"]),
        credits=int(pack["credits"]),
    )
    if existing is None:
        db.add(purchase)
        await db.flush()
    initiated = await payment_provider().initiate(
        purchase.amount_rials,
        str(pack["name_fa"]),
        settings.payment_callback_url,
        str(purchase.id),
    )
    purchase.provider_reference = initiated.authority
    purchase.status = "pending"
    await db.commit()
    return PurchaseResponse(
        purchase_id=purchase.id, payment_url=initiated.payment_url, status=purchase.status
    )


@router.get("/callback", response_model=CallbackResponse)
async def payment_callback(
    request: Request,
    db: Database,
    authority: Annotated[str, Query(alias="Authority", min_length=10)],
    status: Annotated[str, Query(alias="Status")],
    signature: str | None = Query(default=None),
) -> CallbackResponse:
    purchase = await db.scalar(
        select(Purchase).where(Purchase.provider_reference == authority).with_for_update()
    )
    if purchase is None:
        raise ApiError(404, "purchase_not_found", "تراکنش پیدا نشد.")
    if settings.payment_provider == "local":
        provider = payment_provider()
        assert isinstance(provider, LocalPaymentProvider)
        if signature is None or not provider.callback_is_valid(authority, status, signature):
            raise ApiError(403, "forged_callback", "اعتبار پاسخ پرداخت تأیید نشد.")
    if status != "OK":
        purchase.status = "cancelled"
        await db.commit()
        return CallbackResponse(status="cancelled")
    verified = await payment_provider().verify(authority, purchase.amount_rials)
    if not verified.successful:
        purchase.status = "verification_failed"
        await db.commit()
        raise ApiError(409, "payment_not_verified", "پرداخت از سوی درگاه تأیید نشد.")
    await grant_purchase(db, purchase.user_id, purchase.id, purchase.credits)
    purchase.status = "paid"
    purchase.provider_reference = authority
    purchase.callback_payload_digest = (
        request.url.query and hashlib.sha256(request.url.query.encode()).hexdigest()
    )
    purchase.verified_at = purchase.verified_at or datetime.now(UTC)
    await db.commit()
    return CallbackResponse(
        status="paid",
        balance=await credit_balance(db, purchase.user_id),
        reference_id=verified.reference_id,
    )


@router.get("/local/checkout", response_class=HTMLResponse)
async def local_checkout(authority: str) -> HTMLResponse:
    if settings.payment_provider != "local":
        raise ApiError(404, "not_found", "صفحه پیدا نشد.")
    provider = payment_provider()
    assert isinstance(provider, LocalPaymentProvider)
    success_signature = provider.sign_callback(authority, "OK")
    cancel_signature = provider.sign_callback(authority, "NOK")
    callback = settings.payment_callback_url
    html = f"""<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8">
    <title>درگاه آزمایشی آواتو</title><style>body{{font-family:Tahoma;background:#f8f1e7;display:grid;place-items:center;min-height:100vh}}main{{background:white;padding:32px;border-radius:24px;text-align:center}}a{{display:inline-block;margin:8px;padding:12px 20px;border-radius:12px;background:#d95739;color:white;text-decoration:none}}a.cancel{{background:#eee;color:#333}}</style><main><h1>درگاه آزمایشی محلی</h1><p>در این محیط پول واقعی جابه‌جا نمی‌شود.</p><a href="{callback}?Authority={authority}&Status=OK&signature={success_signature}">پرداخت موفق</a><a class="cancel" href="{callback}?Authority={authority}&Status=NOK&signature={cancel_signature}">انصراف</a></main></html>"""
    return HTMLResponse(html)
