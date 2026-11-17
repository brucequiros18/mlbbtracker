"""Verification of Google ID tokens.

The Flutter app signs in with Google Identity Services and sends the resulting
ID token to ``POST /api/v1/auth/google``. The backend verifies it locally:

* the signature against Google's published JWKS (RS256),
* the issuer (``accounts.google.com``),
* the audience (our own OAuth client ID),
* the expiry, and
* that the Google account's email is verified.

Only then does it trust the ``sub`` claim, which is Google's stable subject ID
and the identity key of an account. The token is never stored.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol

import httpx
import jwt

from app.core.errors import GoogleTokenInvalidError, ProviderUnavailableError
from app.core.logging import get_logger

logger = get_logger(__name__)

GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = ("https://accounts.google.com", "accounts.google.com")

# Google rotates signing keys; an hour of caching is plenty and a miss on the
# key id forces an immediate refetch.
_JWKS_TTL_SECONDS = 60 * 60


@dataclass(frozen=True)
class GoogleIdentity:
    """The verified claims we act on."""

    subject: str
    email: str
    email_verified: bool
    name: str | None
    picture: str | None


class GoogleTokenVerifier(Protocol):
    """Anything that can turn a Google credential into verified claims."""

    async def verify(self, credential: str) -> GoogleIdentity: ...


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() == "true"
    return False


class GoogleIdTokenVerifier:
    """Verifies Google ID tokens against Google's JWKS (no network per call)."""

    def __init__(
        self,
        client_id: str,
        *,
        jwks_url: str = GOOGLE_JWKS_URL,
        timeout: float = 10.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        if not client_id:
            raise ValueError("A Google client ID is required to verify tokens.")
        self._client_id = client_id
        self._jwks_url = jwks_url
        self._timeout = timeout
        # Tests inject a MockTransport; production uses httpx's default.
        self._transport = transport
        self._keys: dict[str, jwt.PyJWK] = {}
        self._fetched_at = 0.0

    async def verify(self, credential: str) -> GoogleIdentity:
        try:
            header = jwt.get_unverified_header(credential)
        except jwt.PyJWTError as exc:
            raise GoogleTokenInvalidError(
                "That Google sign-in response could not be read. Please try again."
            ) from exc

        key_id = header.get("kid")
        if header.get("alg") != "RS256" or not key_id:
            raise GoogleTokenInvalidError(
                "That Google sign-in response used an unsupported signature."
            )

        key = await self._key_for(str(key_id))
        try:
            claims = jwt.decode(
                credential,
                key=key,
                algorithms=["RS256"],
                audience=self._client_id,
                issuer=list(GOOGLE_ISSUERS),
                options={"require": ["exp", "iat", "aud", "iss", "sub"]},
            )
        except jwt.PyJWTError as exc:
            logger.info("google id token rejected: %s", exc)
            raise GoogleTokenInvalidError(
                "Google sign-in could not be verified. Please sign in again."
            ) from exc

        subject = claims.get("sub")
        email = claims.get("email")
        if not isinstance(subject, str) or not subject:
            raise GoogleTokenInvalidError("The Google account has no stable identifier.")
        if not isinstance(email, str) or not email:
            raise GoogleTokenInvalidError(
                "Google did not share an email address for this account."
            )
        if not _as_bool(claims.get("email_verified")):
            raise GoogleTokenInvalidError(
                "Your Google email address is not verified, so it cannot be used to sign in."
            )

        name = claims.get("name")
        picture = claims.get("picture")
        return GoogleIdentity(
            subject=subject,
            email=email,
            email_verified=True,
            name=name if isinstance(name, str) else None,
            picture=picture if isinstance(picture, str) else None,
        )

    async def _key_for(self, key_id: str) -> jwt.PyJWK:
        if not self._keys or time.monotonic() - self._fetched_at > _JWKS_TTL_SECONDS:
            await self._refresh_keys()
        key = self._keys.get(key_id)
        if key is None:
            # Google rotated its keys: refetch once before rejecting the token.
            await self._refresh_keys()
            key = self._keys.get(key_id)
        if key is None:
            raise GoogleTokenInvalidError(
                "Google sign-in could not be verified (unknown signing key)."
            )
        return key

    async def _refresh_keys(self) -> None:
        try:
            async with httpx.AsyncClient(
                timeout=self._timeout, transport=self._transport
            ) as client:
                response = await client.get(self._jwks_url)
            response.raise_for_status()
            payload = response.json()
            keyset = jwt.PyJWKSet.from_dict(payload)
        except (httpx.HTTPError, ValueError, jwt.PyJWTError) as exc:
            logger.warning("could not fetch Google JWKS: %s", exc)
            raise ProviderUnavailableError(
                "Could not reach Google to verify the sign-in. Please try again."
            ) from exc
        self._keys = {k.key_id: k for k in keyset.keys if k.key_id}
        self._fetched_at = time.monotonic()
