from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SpeechBoundary:
    start_ms: int
    end_ms: int
    strength: float = 1.0


@dataclass(frozen=True)
class VisualSection:
    position: int
    start_ms: int
    end_ms: int
    media_id: str
    reused: bool


def automatic_sections(
    boundaries: list[SpeechBoundary], media_ids: list[str], duration_ms: int
) -> list[VisualSection]:
    """Assign ordered media at natural boundaries, deterministically.

    Sections never become shorter than 1.2 seconds. When there are fewer media
    than speech sections, items repeat in the original order; when there are more,
    only the useful prefix is assigned and the UI asks the user to remove extras.
    """
    if not media_ids:
        raise ValueError("at least one media item is required")
    if len(media_ids) > 12:
        raise ValueError("at most twelve media items are allowed")
    if duration_ms < 1000:
        raise ValueError("narration is too short")

    candidates = [
        boundary for boundary in boundaries if boundary.end_ms - boundary.start_ms >= 1200
    ]
    if not candidates:
        candidates = [SpeechBoundary(0, duration_ms)]
    candidates[0] = SpeechBoundary(0, candidates[0].end_ms, candidates[0].strength)
    candidates[-1] = SpeechBoundary(candidates[-1].start_ms, duration_ms, candidates[-1].strength)

    result: list[VisualSection] = []
    for position, boundary in enumerate(candidates):
        media_index = position % len(media_ids)
        result.append(
            VisualSection(
                position=position,
                start_ms=boundary.start_ms,
                end_ms=boundary.end_ms,
                media_id=media_ids[media_index],
                reused=position >= len(media_ids),
            )
        )
    return result


def media_count_state(count: int, duration_seconds: float) -> str:
    if count < 1:
        return "missing"
    if count > 12:
        return "too_many"
    recommended_min = 2 if duration_seconds <= 15 else 5 if duration_seconds <= 30 else 8
    if count < recommended_min:
        return "too_few"
    return "recommended"
