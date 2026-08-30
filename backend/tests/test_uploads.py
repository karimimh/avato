import pytest

from app.domain.uploads import UploadRejected, safe_filename, validate_upload


def test_safe_filename_removes_paths_and_preserves_persian() -> None:
    assert safe_filename("../../عکس تولد.jpg") == "عکس-تولد.jpg"
    assert safe_filename("..\\..\\voice note.mp3") == "voice-note.mp3"


def test_valid_jpeg_is_accepted() -> None:
    upload = validate_upload("photo.jpg", "image/jpeg", 120, b"\xff\xd8\xffpayload")
    assert upload.kind == "photo"


def test_spoofed_content_type_is_rejected() -> None:
    with pytest.raises(UploadRejected) as error:
        validate_upload("attack.jpg", "image/jpeg", 120, b"not-an-image")
    assert error.value.code == "content_type_mismatch"


def test_oversized_file_is_rejected() -> None:
    with pytest.raises(UploadRejected) as error:
        validate_upload("photo.jpg", "image/jpeg", 21 * 1024 * 1024, b"\xff\xd8\xff")
    assert error.value.code == "invalid_file_size"
