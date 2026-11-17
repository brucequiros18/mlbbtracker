"""App accounts: Google sign-in, profile setup and sessions.

Google is the **only** credential. Everything else is app-only profile data:

* ``username`` - chosen by the player, unique (case-insensitive);
* ``mlbb_id`` - self-declared and never verified against Moonton;
* ``password`` - stored as a salted scrypt hash, never sent to Moonton, never
  used to sign in; it only confirms changes to the profile.

Sessions are opaque bearer tokens; only their SHA-256 digest is stored.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

from app.core.config import Settings
from app.core.errors import (
    AuthRequiredError,
    GoogleNotConfiguredError,
    InvalidPasswordError,
    ProfileAlreadyCompleteError,
    UsernameTakenError,
)
from app.core.logging import get_logger
from app.core.security import (
    generate_session_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.models import User
from app.db.repo import (
    create_user_session,
    delete_user_session,
    find_user_by_id,
    find_user_by_username,
    find_user_session,
    set_user_profile,
    touch_user_session,
    update_user_profile,
    upsert_google_user,
)
from app.integrations.google_auth import GoogleTokenVerifier

logger = get_logger(__name__)

_GOOGLE_NOT_CONFIGURED = (
    "Google sign-in is not configured on this server yet. "
    "Set MLBB_GOOGLE_CLIENT_ID to the OAuth 2.0 web client ID."
)
_SESSION_EXPIRED = "Your session has expired. Please sign in with Google again."


@dataclass(frozen=True)
class SignInResult:
    session_token: str
    user: User
    is_new_user: bool


class AuthService:
    def __init__(
        self,
        settings: Settings,
        session_factory,
        *,
        verifier: GoogleTokenVerifier | None = None,
    ) -> None:
        self._settings = settings
        self._session_factory = session_factory
        self._verifier = verifier

    @property
    def google_enabled(self) -> bool:
        return bool(self._settings.google_client_id)

    @property
    def _ttl(self) -> dt.timedelta:
        return dt.timedelta(days=self._settings.user_session_ttl_days)

    async def sign_in_with_google(self, credential: str) -> SignInResult:
        """Verify a Google ID token, then create an app session for it."""
        if not self.google_enabled or self._verifier is None:
            raise GoogleNotConfiguredError(_GOOGLE_NOT_CONFIGURED)

        identity = await self._verifier.verify(credential)
        user, created = upsert_google_user(
            self._session_factory,
            google_sub=identity.subject,
            email=identity.email,
            email_verified=identity.email_verified,
            google_name=identity.name,
            picture_url=identity.picture,
        )
        token = generate_session_token()
        create_user_session(
            self._session_factory,
            token_hash=hash_token(token),
            user_id=user.id,
            ttl=self._ttl,
        )
        logger.info("google sign-in: user=%s new=%s", user.id, created)
        return SignInResult(session_token=token, user=user, is_new_user=created)

    def register(
        self,
        token: str,
        *,
        username: str,
        mlbb_id: str,
        password: str,
    ) -> User:
        """Complete the profile of a freshly signed-in Google account."""
        user = self.require_user(token)
        if user.username is not None:
            raise ProfileAlreadyCompleteError(
                "This account already has a profile. Change it with PATCH /api/v1/auth/me."
            )
        self._ensure_username_free(username, user_id=user.id)
        return set_user_profile(
            self._session_factory,
            user.id,
            username=username,
            mlbb_id=mlbb_id,
            password_hash=hash_password(password),
        )

    def require_user(self, token: str) -> User:
        """Resolve a bearer token to its account, or raise 401."""
        if not token:
            raise AuthRequiredError("Sign in with Google to continue.")
        token_digest = hash_token(token)
        session = find_user_session(self._session_factory, token_digest)
        if session is None:
            raise AuthRequiredError(_SESSION_EXPIRED)
        user = find_user_by_id(self._session_factory, session.user_id)
        if user is None:
            raise AuthRequiredError(_SESSION_EXPIRED)
        touch_user_session(
            self._session_factory, token_hash=token_digest, ttl=self._ttl
        )
        return user

    def update_profile(
        self,
        token: str,
        *,
        username: str | None,
        mlbb_id: str | None,
        current_password: str,
        new_password: str | None,
    ) -> User:
        """Change profile fields, confirmed with the app password."""
        user = self.require_user(token)
        if not verify_password(current_password, user.password_hash):
            raise InvalidPasswordError(
                "That app password did not match, so nothing was changed."
            )
        if username is not None and username != user.username:
            self._ensure_username_free(username, user_id=user.id)
        return update_user_profile(
            self._session_factory,
            user.id,
            username=username,
            mlbb_id=mlbb_id,
            password_hash=hash_password(new_password) if new_password else None,
        )

    def sign_out(self, token: str) -> None:
        if token:
            delete_user_session(self._session_factory, hash_token(token))

    def _ensure_username_free(self, username: str, *, user_id: int) -> None:
        existing = find_user_by_username(self._session_factory, username)
        if existing is not None and existing.id != user_id:
            raise UsernameTakenError(f"@{username} is already taken.")
