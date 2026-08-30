from __future__ import annotations

from typing import Any

import httpx

from app.payments.base import PaymentInitiation, PaymentVerification


class ZarinpalPaymentProvider:
    """Zarinpal v4 adapter.

    Contract reviewed against the official request/verify and sandbox documentation:
    https://www.zarinpal.com/docs/paymentGateway/connectToGateway
    https://www.zarinpal.com/docs/paymentGateway/sandBox
    """

    def __init__(
        self, merchant_id: str, sandbox: bool = False, client: httpx.AsyncClient | None = None
    ) -> None:
        if not merchant_id:
            raise ValueError("ZARINPAL_MERCHANT_ID is required")
        self.merchant_id = merchant_id
        host = "https://sandbox.zarinpal.com" if sandbox else "https://payment.zarinpal.com"
        self.api_base = f"{host}/pg/v4/payment"
        self.start_base = f"{host}/pg/StartPay"
        self.client = client or httpx.AsyncClient(timeout=15)

    async def initiate(
        self, amount_rials: int, description: str, callback_url: str, order_id: str
    ) -> PaymentInitiation:
        response = await self.client.post(
            f"{self.api_base}/request.json",
            json={
                "merchant_id": self.merchant_id,
                "amount": amount_rials,
                "currency": "IRR",
                "description": description,
                "callback_url": callback_url,
                "metadata": {"order_id": order_id, "auto_verify": False},
            },
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        payload: dict[str, Any] = response.json()
        data = payload.get("data", {})
        if data.get("code") != 100 or not data.get("authority"):
            raise RuntimeError("Zarinpal refused payment initiation")
        authority = str(data["authority"])
        return PaymentInitiation(authority, f"{self.start_base}/{authority}")

    async def verify(self, authority: str, amount_rials: int) -> PaymentVerification:
        response = await self.client.post(
            f"{self.api_base}/verify.json",
            json={
                "merchant_id": self.merchant_id,
                "amount": amount_rials,
                "authority": authority,
            },
            headers={"Accept": "application/json"},
        )
        response.raise_for_status()
        data: dict[str, Any] = response.json().get("data", {})
        code = int(data.get("code", -1))
        return PaymentVerification(
            successful=code in {100, 101},
            already_verified=code == 101,
            reference_id=str(data["ref_id"]) if data.get("ref_id") is not None else None,
            raw_code=code,
        )
