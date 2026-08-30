from __future__ import annotations

import asyncio
import os
import uuid
import wave
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.api.payments import payment_provider
from app.db.models import AnalyticsEvent, Project, User
from app.db.session import async_session_factory, engine
from app.main import app
from app.payments.local import LocalPaymentProvider
from app.services.credits import charge_successful_export, credit_balance, grant_purchase
from app.workers.retention_tasks import _delete_expired_projects, _warn_expiring_projects

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_DB_TESTS") != "1", reason="requires migrated PostgreSQL and MinIO"
)


@pytest_asyncio.fixture(autouse=True)
async def dispose_connections() -> AsyncIterator[None]:
    yield
    await engine.dispose()


async def register(client: AsyncClient, label: str) -> tuple[str, uuid.UUID]:
    response = await client.post(
        "/api/auth/register",
        json={"email": f"{label}-{uuid.uuid4()}@example.test", "password": "correct-horse-123"},
    )
    assert response.status_code == 201, response.text
    return response.json()["token"], uuid.UUID(response.json()["user"]["id"])


def voice_fixture(path: Path, seconds: int = 6) -> bytes:
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(16_000)
        output.writeframes(b"\x00\x00" * 16_000 * seconds)
    return path.read_bytes()


@pytest.mark.asyncio
async def test_project_ownership_and_repeat_safe_deletion() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        owner_token, owner_id = await register(client, "owner")
        other_token, other_id = await register(client, "other")
        created = await client.post(
            "/api/projects",
            headers={"Authorization": f"Bearer {owner_token}"},
            json={"duration_limit_seconds": 30},
        )
        assert created.status_code == 201
        project_id = created.json()["id"]
        hidden = await client.get(
            f"/api/projects/{project_id}",
            headers={"Authorization": f"Bearer {other_token}"},
        )
        assert hidden.status_code == 404
        deleted = await client.delete(
            f"/api/projects/{project_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert deleted.status_code == 200 and deleted.json() == {"deleted": True}
        missing = await client.get(
            f"/api/projects/{project_id}",
            headers={"Authorization": f"Bearer {owner_token}"},
        )
        assert missing.status_code == 404
        for token in (owner_token, other_token):
            response = await client.delete(
                "/api/auth/account", headers={"Authorization": f"Bearer {token}"}
            )
            assert response.status_code == 200
    async with async_session_factory() as db:
        assert await db.get(User, owner_id) is None
        assert await db.get(User, other_id) is None


@pytest.mark.asyncio
async def test_audio_trim_is_bounded_and_requeues_processing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    queued: list[str] = []
    monkeypatch.setattr("app.api.assets.process_audio_task.delay", queued.append)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token, _ = await register(client, "trim")
        headers = {"Authorization": f"Bearer {token}"}
        created = await client.post(
            "/api/projects",
            headers=headers,
            json={"duration_limit_seconds": 15},
        )
        project_id = created.json()["id"]
        uploaded = await client.put(
            f"/api/projects/{project_id}/audio",
            headers={**headers, "Content-Type": "audio/wav", "X-Filename": "voice.wav"},
            content=voice_fixture(tmp_path / "voice.wav"),
        )
        assert uploaded.status_code == 200, uploaded.text
        audio_id = uploaded.json()["id"]

        too_short = await client.patch(
            f"/api/projects/{project_id}/audio/{audio_id}/trim",
            headers=headers,
            json={"start_ms": 1000, "end_ms": 4000},
        )
        assert too_short.status_code == 422
        trimmed = await client.patch(
            f"/api/projects/{project_id}/audio/{audio_id}/trim",
            headers=headers,
            json={"start_ms": 500, "end_ms": 5500},
        )
        assert trimmed.status_code == 200, trimmed.text
        assert trimmed.json()["trim_start_ms"] == 500
        assert trimmed.json()["trim_end_ms"] == 5500
        listed = await client.get(f"/api/projects/{project_id}/audio", headers=headers)
        assert listed.status_code == 200
        assert listed.json()[0]["url"].startswith("http://localhost:9100/")
        assert queued == [audio_id, audio_id]
        deleted = await client.delete("/api/auth/account", headers=headers)
        assert deleted.status_code == 200


@pytest.mark.asyncio
async def test_retention_warns_then_deletes_expired_private_project() -> None:
    user_id = uuid.uuid4()
    project_id = uuid.uuid4()
    async with async_session_factory() as db:
        db.add(
            User(
                id=user_id,
                email=f"retention-{user_id}@example.test",
                password_hash="not-used",
            )
        )
        db.add(
            Project(
                id=project_id,
                user_id=user_id,
                duration_limit_seconds=15,
                template_id="clean-story",
                last_activity_at=datetime.now(UTC),
                expires_at=datetime.now(UTC) + timedelta(days=2),
            )
        )
        await db.commit()

    assert await _warn_expiring_projects() == {"warned": 1}
    async with async_session_factory() as db:
        project = await db.get(Project, project_id)
        assert project is not None and project.expiry_warned_at is not None
        warning = await db.scalar(
            select(AnalyticsEvent).where(
                AnalyticsEvent.project_id == project_id,
                AnalyticsEvent.name == "expiry_warning_due",
            )
        )
        assert warning is not None
        project.expires_at = datetime.now(UTC) - timedelta(seconds=1)
        await db.commit()

    assert await _delete_expired_projects() == {"deleted": 1}
    async with async_session_factory() as db:
        assert await db.get(Project, project_id) is None
        user = await db.get(User, user_id)
        assert user is not None
        await db.delete(user)
        await db.commit()


@pytest.mark.asyncio
async def test_concurrent_paid_export_charges_once() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token, user_id = await register(client, "credits")
        project_response = await client.post(
            "/api/projects",
            headers={"Authorization": f"Bearer {token}"},
            json={"duration_limit_seconds": 15},
        )
        project_id = uuid.UUID(project_response.json()["id"])

    async with async_session_factory() as db:
        assert await db.scalar(select(Project.id).where(Project.id == project_id))
        await grant_purchase(db, user_id, uuid.uuid4(), 2)
        await db.commit()

    async def charge(export_id: uuid.UUID) -> bool:
        async with async_session_factory() as db:
            charged = await charge_successful_export(db, user_id, project_id, export_id)
            await db.commit()
            return charged

    outcomes = await asyncio.gather(charge(uuid.uuid4()), charge(uuid.uuid4()))
    assert sorted(outcomes) == [False, True]
    async with async_session_factory() as db:
        assert await credit_balance(db, user_id) == 1
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (
            await client.delete("/api/auth/account", headers={"Authorization": f"Bearer {token}"})
        ).status_code == 200


@pytest.mark.asyncio
async def test_payment_forgery_duplicate_callback_and_credit_grant() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token, user_id = await register(client, "payment")
        purchase = await client.post(
            "/api/payments/purchases",
            headers={"Authorization": f"Bearer {token}", "Idempotency-Key": str(uuid.uuid4())},
            json={"pack_id": "small"},
        )
        assert purchase.status_code == 201
        authority = parse_qs(urlparse(purchase.json()["payment_url"]).query)["authority"][0]
        forged = await client.get(
            "/api/payments/callback",
            params={"Authority": authority, "Status": "OK", "signature": "forged"},
        )
        assert forged.status_code == 403
        provider = payment_provider()
        assert isinstance(provider, LocalPaymentProvider)
        signature = provider.sign_callback(authority, "OK")
        first = await client.get(
            "/api/payments/callback",
            params={"Authority": authority, "Status": "OK", "signature": signature},
        )
        duplicate = await client.get(
            "/api/payments/callback",
            params={"Authority": authority, "Status": "OK", "signature": signature},
        )
        assert first.status_code == 200 and first.json()["balance"] == 1
        assert duplicate.status_code == 200 and duplicate.json()["balance"] == 1
        await client.delete("/api/auth/account", headers={"Authorization": f"Bearer {token}"})
    async with async_session_factory() as db:
        assert await db.get(User, user_id) is None
