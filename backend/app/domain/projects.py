from __future__ import annotations

from datetime import UTC, datetime, timedelta

PROJECT_RETENTION_DAYS = 30

PROJECT_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"transcribing", "editing"}),
    "transcribing": frozenset({"editing", "failed"}),
    "editing": frozenset({"transcribing", "rendering"}),
    "rendering": frozenset({"ready", "failed", "cancelled"}),
    "ready": frozenset({"editing", "rendering"}),
    "failed": frozenset({"editing", "rendering"}),
    "cancelled": frozenset({"editing", "rendering"}),
}


class InvalidProjectTransition(ValueError):
    def __init__(self, current: str, target: str) -> None:
        super().__init__(f"project cannot transition from {current!r} to {target!r}")
        self.current = current
        self.target = target


def validate_project_transition(current: str, target: str) -> None:
    if target == current:
        return
    if target not in PROJECT_TRANSITIONS.get(current, frozenset()):
        raise InvalidProjectTransition(current, target)


def activity_expiry(now: datetime | None = None) -> datetime:
    current = now or datetime.now(UTC)
    return current + timedelta(days=PROJECT_RETENTION_DAYS)


def media_recommendation(duration_seconds: float) -> tuple[int, int]:
    """Return the useful inclusive range without exceeding the 1–12 contract."""
    if duration_seconds <= 15:
        return (2, 4)
    if duration_seconds <= 30:
        return (5, 8)
    return (8, 12)
