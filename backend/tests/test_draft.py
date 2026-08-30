import pytest

from app.domain.draft import SpeechBoundary, automatic_sections, media_count_state


@pytest.mark.parametrize("duration", [15_000, 30_000, 60_000])
def test_assignment_is_deterministic_and_preserves_order(duration: int) -> None:
    boundaries = [
        SpeechBoundary(start, min(start + 5000, duration)) for start in range(0, duration, 5000)
    ]
    first = automatic_sections(boundaries, ["a", "b", "c"], duration)
    second = automatic_sections(boundaries, ["a", "b", "c"], duration)
    assert first == second
    assert [section.media_id for section in first[:3]] == ["a", "b", "c"]
    assert first[0].start_ms == 0
    assert first[-1].end_ms == duration


def test_too_few_media_is_reused_in_order() -> None:
    sections = automatic_sections(
        [SpeechBoundary(0, 3000), SpeechBoundary(3000, 6000), SpeechBoundary(6000, 9000)],
        ["a", "b"],
        9000,
    )
    assert [(item.media_id, item.reused) for item in sections] == [
        ("a", False),
        ("b", False),
        ("a", True),
    ]


@pytest.mark.parametrize(
    ("count", "duration", "state"),
    [(0, 30, "missing"), (13, 30, "too_many"), (1, 30, "too_few"), (5, 30, "recommended")],
)
def test_media_count_guidance(count: int, duration: float, state: str) -> None:
    assert media_count_state(count, duration) == state
