from app.core.security import (
    digest_session_token,
    hash_password,
    new_session_token,
    verify_password,
)


def test_password_hash_is_salted_and_verifiable() -> None:
    first = hash_password("a secure password")
    second = hash_password("a secure password")
    assert first != second
    assert verify_password("a secure password", first)
    assert not verify_password("wrong password", first)


def test_session_stores_digest_not_plaintext() -> None:
    token = new_session_token()
    assert token.plaintext.encode() not in token.digest
    assert digest_session_token(token.plaintext) == token.digest
