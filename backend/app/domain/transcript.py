from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Segment:
    id: str
    position: int
    start_ms: int
    end_ms: int
    text: str
    original_text: str
    confidence: float


def edit_segment(segment: Segment, text: str) -> Segment:
    cleaned = " ".join(text.split())
    if not cleaned:
        raise ValueError("subtitle text cannot be empty")
    return replace(segment, text=cleaned)


def restore_segment(segment: Segment) -> Segment:
    return replace(segment, text=segment.original_text)


def split_segment(segment: Segment, character_index: int) -> tuple[Segment, Segment]:
    left_text = segment.text[:character_index].strip()
    right_text = segment.text[character_index:].strip()
    if not left_text or not right_text:
        raise ValueError("split must leave text on both sides")
    ratio = len(left_text) / (len(left_text) + len(right_text))
    split_ms = segment.start_ms + round((segment.end_ms - segment.start_ms) * ratio)
    if split_ms <= segment.start_ms or split_ms >= segment.end_ms:
        raise ValueError("split timing is too short")
    return (
        replace(segment, id=f"{segment.id}-a", end_ms=split_ms, text=left_text),
        replace(
            segment,
            id=f"{segment.id}-b",
            position=segment.position + 1,
            start_ms=split_ms,
            text=right_text,
        ),
    )


def merge_segments(first: Segment, second: Segment) -> Segment:
    if second.position != first.position + 1 or second.start_ms < first.end_ms:
        raise ValueError("only adjacent, non-overlapping segments can be merged")
    return Segment(
        id=first.id,
        position=first.position,
        start_ms=first.start_ms,
        end_ms=second.end_ms,
        text=f"{first.text} {second.text}",
        original_text=f"{first.original_text} {second.original_text}",
        confidence=min(first.confidence, second.confidence),
    )
