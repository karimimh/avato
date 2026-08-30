from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CreditLedgerEntry, User
from app.domain.credits import InsufficientCredits


async def credit_balance(db: AsyncSession, user_id: uuid.UUID) -> int:
    value = await db.scalar(
        select(func.coalesce(func.sum(CreditLedgerEntry.amount), 0)).where(
            CreditLedgerEntry.user_id == user_id
        )
    )
    return int(value or 0)


async def grant_purchase(
    db: AsyncSession, user_id: uuid.UUID, purchase_id: uuid.UUID, credits: int
) -> bool:
    key = f"purchase:{purchase_id}"
    if await db.scalar(
        select(CreditLedgerEntry.id).where(
            CreditLedgerEntry.user_id == user_id, CreditLedgerEntry.idempotency_key == key
        )
    ):
        return False
    db.add(
        CreditLedgerEntry(
            user_id=user_id,
            amount=credits,
            reason="purchase",
            reference_type="purchase",
            reference_id=str(purchase_id),
            idempotency_key=key,
        )
    )
    await db.flush()
    return True


async def charge_successful_export(
    db: AsyncSession,
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    export_id: uuid.UUID,
) -> bool:
    # The user-row lock serializes concurrent exports for one account. Unique
    # ledger keys remain the final idempotency guard across process retries.
    await db.scalar(select(User.id).where(User.id == user_id).with_for_update())
    prior_project_charge = await db.scalar(
        select(CreditLedgerEntry.id).where(
            CreditLedgerEntry.user_id == user_id,
            CreditLedgerEntry.reason == "export_charge",
            CreditLedgerEntry.reference_type == "project",
            CreditLedgerEntry.reference_id == str(project_id),
        )
    )
    if prior_project_charge is not None:
        return False
    if await credit_balance(db, user_id) < 1:
        raise InsufficientCredits("paid export requires one credit")
    db.add(
        CreditLedgerEntry(
            user_id=user_id,
            amount=-1,
            reason="export_charge",
            reference_type="project",
            reference_id=str(project_id),
            idempotency_key=f"export:{export_id}",
        )
    )
    await db.flush()
    return True
