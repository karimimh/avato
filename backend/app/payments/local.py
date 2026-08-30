from __future__ import annotations

import hashlib
import hmac
import secrets
from urllib.parse import urlencode

from app.payments.base import PaymentInitiation, PaymentVerification


class LocalPaymentProvider:
    """Deterministic local boundary with signed callbacks and duplicate handling."""

    def __init__(self, secret: str, base_url: str = "http://localhost:8080") -> None:
        self.secret = secret.encode()
        self.base_url = base_url.rstrip("/")
        self._verified: set[str] = set()

    def sign_callback(self, authority: str, status: str) -> str:
        return hmac.new(self.secret, f"{authority}:{status}".encode(), hashlib.sha256).hexdigest()

    def callback_is_valid(self, authority: str, status: str, signature: str) -> bool:
        return hmac.compare_digest(self.sign_callback(authority, status), signature)

    async def initiate(
        self, amount_rials: int, description: str, callback_url: str, order_id: str
    ) -> PaymentInitiation:
        del description, callback_url
        if amount_rials <= 0:
            raise ValueError("payment amount must be positive")
        authority = f"S{secrets.token_hex(17)}"
        query = urlencode({"authority": authority, "order_id": order_id})
        return PaymentInitiation(authority, f"{self.base_url}/api/payments/local/checkout?{query}")

    async def verify(self, authority: str, amount_rials: int) -> PaymentVerification:
        if amount_rials <= 0 or not authority.startswith("S"):
            return PaymentVerification(False, False, None, -1)
        duplicate = authority in self._verified
        self._verified.add(authority)
        reference = hashlib.sha256(authority.encode()).hexdigest()[:16]
        return PaymentVerification(True, duplicate, reference, 101 if duplicate else 100)
