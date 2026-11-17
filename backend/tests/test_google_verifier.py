"""The real Google ID-token verifier, offline.

A locally generated RSA key signs the tokens and a MockTransport serves the
JWKS, so the signature, issuer, audience, expiry and key-rotation paths are all
exercised without touching Google.
"""

from __future__ import annotations

import base64
import time

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core.errors import GoogleTokenInvalidError, ProviderUnavailableError
from app.integrations.google_auth import GoogleIdTokenVerifier

CLIENT_ID = "test-client.apps.googleusercontent.com"
KID = "test-kid-1"


def _b64u(value: int) -> str:
    raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


@pytest.fixture(scope="module")
def keypair():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    numbers = private.public_key().public_numbers()
    jwk = {
        "kty": "RSA",
        "kid": KID,
        "use": "sig",
        "alg": "RS256",
        "n": _b64u(numbers.n),
        "e": _b64u(numbers.e),
    }
    return private, {"keys": [jwk]}


def _claims(**overrides):
    now = int(time.time())
    claims = {
        "iss": "https://accounts.google.com",
        "aud": CLIENT_ID,
        "sub": "google-sub-42",
        "email": "verified@example.com",
        "email_verified": True,
        "iat": now,
        "exp": now + 600,
        "name": "Verified Player",
        "picture": "https://img.example/p.png",
    }
    claims.update(overrides)
    return claims


def _token(private, **overrides) -> str:
    headers = {"kid": overrides.pop("kid", KID)}
    return jwt.encode(
        _claims(**overrides), private, algorithm="RS256", headers=headers
    )


def _verifier(jwks, *, calls=None, status=200):
    def handler(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls.append(request.url)
        return httpx.Response(status, json=jwks)

    return GoogleIdTokenVerifier(
        CLIENT_ID,
        jwks_url="https://keys.example.test/certs",
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.asyncio
async def test_valid_token_yields_identity(keypair):
    private, jwks = keypair
    identity = await _verifier(jwks).verify(_token(private))
    assert identity.subject == "google-sub-42"
    assert identity.email == "verified@example.com"
    assert identity.email_verified is True
    assert identity.name == "Verified Player"
    assert identity.picture == "https://img.example/p.png"


@pytest.mark.asyncio
async def test_jwks_is_cached_between_tokens(keypair):
    private, jwks = keypair
    calls: list[httpx.URL] = []
    verifier = _verifier(jwks, calls=calls)
    await verifier.verify(_token(private))
    await verifier.verify(_token(private))
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_unknown_key_id_forces_one_refetch(keypair):
    private, jwks = keypair
    calls: list[httpx.URL] = []
    verifier = _verifier(jwks, calls=calls)
    with pytest.raises(GoogleTokenInvalidError):
        await verifier.verify(_token(private, kid="rotated-away"))
    assert len(calls) == 2


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "overrides",
    [
        {"aud": "someone-else.apps.googleusercontent.com"},
        {"iss": "https://evil.example"},
        {"exp": int(time.time()) - 60},
        {"email_verified": False},
        {"email_verified": "false"},
        {"sub": ""},
        {"email": ""},
    ],
)
async def test_rejected_claims(keypair, overrides):
    private, jwks = keypair
    with pytest.raises(GoogleTokenInvalidError):
        await _verifier(jwks).verify(_token(private, **overrides))


@pytest.mark.asyncio
async def test_rejects_missing_email_claim(keypair):
    private, jwks = keypair
    token = jwt.encode(
        {k: v for k, v in _claims().items() if k != "email"},
        private,
        algorithm="RS256",
        headers={"kid": KID},
    )
    with pytest.raises(GoogleTokenInvalidError):
        await _verifier(jwks).verify(token)


@pytest.mark.asyncio
async def test_rejects_garbage_and_wrong_algorithm(keypair):
    private, jwks = keypair
    verifier = _verifier(jwks)
    with pytest.raises(GoogleTokenInvalidError):
        await verifier.verify("not-a-jwt")
    with pytest.raises(GoogleTokenInvalidError):
        await verifier.verify(
            jwt.encode(
                _claims(),
                "a-shared-secret-long-enough-for-hs256",
                algorithm="HS256",
                headers={"kid": KID},
            )
        )


@pytest.mark.asyncio
async def test_jwks_outage_is_a_503_not_a_verification_failure(keypair):
    _, _jwks = keypair
    verifier = _verifier({}, status=503)
    with pytest.raises(ProviderUnavailableError):
        await verifier.verify(_token(keypair[0]))
