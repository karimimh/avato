from __future__ import annotations

from dataclasses import dataclass
from typing import BinaryIO, Protocol


@dataclass(frozen=True)
class ObjectInfo:
    key: str
    size: int
    content_type: str
    checksum_sha256: str


class ObjectStorage(Protocol):
    def put_private(self, key: str, body: BinaryIO, content_type: str) -> ObjectInfo: ...

    def delete(self, key: str) -> None: ...

    def delete_prefix(self, prefix: str) -> int: ...

    def read(self, key: str) -> bytes: ...

    def presigned_get(self, key: str, expires_seconds: int = 300) -> str: ...
