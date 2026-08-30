from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

MAX_AUDIO_BYTES = 30 * 1024 * 1024
MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_VIDEO_BYTES = 100 * 1024 * 1024
MAX_MEDIA_ITEMS = 12

ALLOWED_AUDIO = frozenset({"audio/mpeg", "audio/mp4", "audio/wav", "audio/webm", "audio/ogg"})
ALLOWED_IMAGE = frozenset({"image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"})
ALLOWED_VIDEO = frozenset({"video/mp4", "video/quicktime", "video/webm"})


class UploadRejected(ValueError):
    def __init__(self, code: str, message_fa: str) -> None:
        super().__init__(message_fa)
        self.code = code
        self.message_fa = message_fa


@dataclass(frozen=True)
class ValidatedUpload:
    filename: str
    content_type: str
    size_bytes: int
    kind: str


def safe_filename(value: str) -> str:
    basename = Path(unquote(value).replace("\\", "/")).name
    normalized = unicodedata.normalize("NFKC", basename)
    cleaned = re.sub(r"[^\w.\-\u0600-\u06ff]+", "-", normalized, flags=re.UNICODE).strip(".-")
    return cleaned[:180] or "upload"


def _has_matching_signature(content_type: str, head: bytes) -> bool:
    signatures = {
        "image/jpeg": (b"\xff\xd8\xff",),
        "image/png": (b"\x89PNG\r\n\x1a\n",),
        "image/webp": (b"RIFF",),
        "audio/wav": (b"RIFF",),
        "audio/mpeg": (b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"),
        "audio/ogg": (b"OggS",),
        "video/webm": (b"\x1aE\xdf\xa3",),
        "audio/webm": (b"\x1aE\xdf\xa3",),
    }
    if content_type in {"audio/mp4", "video/mp4", "video/quicktime", "image/heic", "image/heif"}:
        return len(head) >= 12 and head[4:8] == b"ftyp"
    return any(head.startswith(signature) for signature in signatures.get(content_type, ()))


def validate_upload(
    filename: str, content_type: str, size_bytes: int, head: bytes
) -> ValidatedUpload:
    if content_type in ALLOWED_AUDIO:
        kind, limit = "audio", MAX_AUDIO_BYTES
    elif content_type in ALLOWED_IMAGE:
        kind, limit = "photo", MAX_IMAGE_BYTES
    elif content_type in ALLOWED_VIDEO:
        kind, limit = "clip", MAX_VIDEO_BYTES
    else:
        raise UploadRejected("unsupported_media_type", "فرمت این فایل پشتیبانی نمی‌شود.")
    if size_bytes <= 0 or size_bytes > limit:
        raise UploadRejected("invalid_file_size", "حجم فایل خارج از محدودهٔ مجاز است.")
    if not _has_matching_signature(content_type, head):
        raise UploadRejected("content_type_mismatch", "محتوای فایل با فرمت اعلام‌شده هماهنگ نیست.")
    return ValidatedUpload(safe_filename(filename), content_type, size_bytes, kind)
