from datetime import UTC, datetime, timedelta

import pytest

from app.domain.projects import (
    InvalidProjectTransition,
    activity_expiry,
    media_recommendation,
    validate_project_transition,
)


def test_valid_project_lifecycle_and_retry_paths() -> None:
    for current, target in [
        ("draft", "transcribing"),
        ("transcribing", "editing"),
        ("editing", "rendering"),
        ("rendering", "ready"),
        ("rendering", "failed"),
        ("failed", "rendering"),
        ("ready", "editing"),
    ]:
        validate_project_transition(current, target)


def test_invalid_transition_is_rejected() -> None:
    with pytest.raises(InvalidProjectTransition):
        validate_project_transition("draft", "ready")


def test_activity_expiry_is_exactly_thirty_days() -> None:
    now = datetime(2026, 8, 30, tzinfo=UTC)
    assert activity_expiry(now) == now + timedelta(days=30)


@pytest.mark.parametrize(
    ("duration", "expected"), [(5, (2, 4)), (15, (2, 4)), (30, (5, 8)), (60, (8, 12))]
)
def test_media_recommendation(duration: float, expected: tuple[int, int]) -> None:
    assert media_recommendation(duration) == expected
