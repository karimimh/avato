from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class PaymentInitiation:
    authority: str
    payment_url: str


@dataclass(frozen=True)
class PaymentVerification:
    successful: bool
    already_verified: bool
    reference_id: str | None
    raw_code: int


class PaymentProvider(Protocol):
    async def initiate(
        self, amount_rials: int, description: str, callback_url: str, order_id: str
    ) -> PaymentInitiation: ...

    async def verify(self, authority: str, amount_rials: int) -> PaymentVerification: ...
