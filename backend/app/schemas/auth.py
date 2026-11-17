"""Account schemas (Google-only sign-in).

`mlbbIdVerified` is always false and exists so clients never have to guess:
the MLBB ID is typed in by the player and is not checked against Moonton.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.core.security import MAX_PASSWORD_LENGTH, MIN_PASSWORD_LENGTH
from app.db.models import User
from app.schemas.common import ApiModel

USERNAME_PATTERN = r"^[A-Za-z0-9_]{3,24}$"
MLBB_ID_PATTERN = r"^\d{4,20}$"


class UserAccount(ApiModel):
    id: int
    email: str
    google_name: str | None = None
    picture_url: str | None = None
    username: str | None = None
    mlbb_id: str | None = None
    profile_complete: bool
    mlbb_id_verified: bool = False
    created_at: datetime
    last_login_at: datetime

    @classmethod
    def from_user(cls, user: User) -> "UserAccount":
        return cls(
            id=user.id,
            email=user.email,
            google_name=user.google_name,
            picture_url=user.picture_url,
            username=user.username,
            mlbb_id=user.mlbb_id,
            profile_complete=bool(
                user.username and user.mlbb_id and user.password_hash
            ),
            mlbb_id_verified=False,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        )


class AuthConfig(ApiModel):
    """What the client needs to render the sign-in screen honestly."""

    google_sign_in_enabled: bool
    google_client_id: str | None = None
    min_password_length: int = MIN_PASSWORD_LENGTH
    max_password_length: int = MAX_PASSWORD_LENGTH
    username_pattern: str = USERNAME_PATTERN
    mlbb_id_pattern: str = MLBB_ID_PATTERN


class GoogleSignInRequest(ApiModel):
    """The ID token produced by Google Identity Services on the device."""

    credential: str = Field(min_length=20, max_length=8192)


class AuthSession(ApiModel):
    session_token: str
    user: UserAccount
    is_new_user: bool


class RegisterRequest(ApiModel):
    username: str = Field(min_length=3, max_length=24, pattern=USERNAME_PATTERN)
    mlbb_id: str = Field(pattern=MLBB_ID_PATTERN)
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)


class UpdateProfileRequest(ApiModel):
    username: str | None = Field(
        default=None, min_length=3, max_length=24, pattern=USERNAME_PATTERN
    )
    mlbb_id: str | None = Field(default=None, pattern=MLBB_ID_PATTERN)
    # The app password confirms the change. It is not a login credential.
    current_password: str = Field(min_length=1, max_length=MAX_PASSWORD_LENGTH)
    new_password: str | None = Field(
        default=None, min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH
    )
