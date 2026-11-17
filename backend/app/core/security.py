"""Password hashing and opaque session tokens.

The app password is **app-only**. It is never sent to Moonton, never used to
sign in (Google is the only credential) and never stored in plaintext: only a
salted scrypt hash is kept. ``verify_password`` is used when a signed-in user
confirms a change to their profile.

Session tokens are random opaque strings; the database stores only their
SHA-256 digest, exactly like the consented player sessions.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

# scrypt parameters (RFC 7914): ~16 MiB of memory per hash, well under
# OpenSSL's 32 MiB default limit, and fast enough for interactive use.
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_DKLEN = 32
_SALT_BYTES = 16

MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128

_TOKEN_BYTES = 32


def _b64encode(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"), validate=True)


def hash_password(password: str) -> str:
    """Return a self-describing scrypt hash: ``scrypt$n$r$p$salt$hash``."""
    if not password:
        raise ValueError("Password must not be empty.")
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=_SCRYPT_DKLEN,
    )
    return "$".join(
        [
            "scrypt",
            str(_SCRYPT_N),
            str(_SCRYPT_R),
            str(_SCRYPT_P),
            _b64encode(salt),
            _b64encode(digest),
        ]
    )


def verify_password(password: str, encoded: str | None) -> bool:
    """Check a password against a stored hash, in constant time."""
    if not password or not encoded:
        return False
    try:
        scheme, n_raw, r_raw, p_raw, salt_raw, digest_raw = encoded.split("$")
        if scheme != "scrypt":
            return False
        n, r, p = int(n_raw), int(r_raw), int(p_raw)
        salt = _b64decode(salt_raw)
        expected = _b64decode(digest_raw)
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p,
            dklen=len(expected),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def generate_session_token() -> str:
    """A new opaque bearer token (never stored as-is)."""
    return secrets.token_urlsafe(_TOKEN_BYTES)


def hash_token(token: str) -> str:
    """SHA-256 digest of a session token, for storage and lookup."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
