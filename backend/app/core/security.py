from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1


def hash_password(password: str) -> str:
    if len(password) < 8 or len(password) > 200:
        raise ValueError("password must contain between 8 and 200 characters")
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode(), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, dklen=32
    )
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, n, r, p, salt_hex, expected_hex = encoded.split("$")
        if algorithm != "scrypt":
            return False
        actual = hashlib.scrypt(
            password.encode(),
            salt=bytes.fromhex(salt_hex),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=32,
        )
        return hmac.compare_digest(actual, bytes.fromhex(expected_hex))
    except (ValueError, TypeError):
        return False


@dataclass(frozen=True)
class SessionToken:
    plaintext: str
    digest: bytes


def new_session_token() -> SessionToken:
    plaintext = secrets.token_urlsafe(32)
    return SessionToken(plaintext, digest_session_token(plaintext))


def digest_session_token(token: str) -> bytes:
    return hashlib.sha256(token.encode()).digest()
