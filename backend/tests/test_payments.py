import pytest

from app.payments.local import LocalPaymentProvider


@pytest.mark.asyncio
async def test_local_callback_rejects_forgery_and_accepts_valid_signature() -> None:
    provider = LocalPaymentProvider("test-secret")
    initiated = await provider.initiate(100_000, "سه اعتبار", "/callback", "order-1")
    signature = provider.sign_callback(initiated.authority, "OK")
    assert provider.callback_is_valid(initiated.authority, "OK", signature)
    assert not provider.callback_is_valid(initiated.authority, "OK", "forged")


@pytest.mark.asyncio
async def test_local_verification_marks_duplicate_callback() -> None:
    provider = LocalPaymentProvider("test-secret")
    initiated = await provider.initiate(100_000, "سه اعتبار", "/callback", "order-1")
    first = await provider.verify(initiated.authority, 100_000)
    duplicate = await provider.verify(initiated.authority, 100_000)
    assert first.successful and not first.already_verified and first.raw_code == 100
    assert duplicate.successful and duplicate.already_verified and duplicate.raw_code == 101
