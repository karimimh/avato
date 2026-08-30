import pytest

from app.domain.transcript import (
    Segment,
    edit_segment,
    merge_segments,
    restore_segment,
    split_segment,
)


def fixture_segment() -> Segment:
    return Segment("one", 0, 1000, 5000, "سلام دوست خوبم", "سلام دوست خوبم", 0.72)


def test_edit_and_restore_preserve_original() -> None:
    edited = edit_segment(fixture_segment(), "  سلام   خواهر خوبم ")
    assert edited.text == "سلام خواهر خوبم"
    assert restore_segment(edited).text == "سلام دوست خوبم"


def test_split_distributes_time_by_text_length() -> None:
    first, second = split_segment(fixture_segment(), 4)
    assert first.text == "سلام"
    assert second.text == "دوست خوبم"
    assert first.end_ms == second.start_ms
    assert first.start_ms == 1000 and second.end_ms == 5000


def test_merge_requires_adjacent_segments() -> None:
    first, second = split_segment(fixture_segment(), 4)
    merged = merge_segments(first, second)
    assert merged.text == "سلام دوست خوبم"
    with pytest.raises(ValueError):
        merge_segments(second, first)
