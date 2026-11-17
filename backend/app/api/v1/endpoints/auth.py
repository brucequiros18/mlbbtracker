"""Account endpoints - Google-only sign-in.

    1. GET   /auth/config    is Google sign-in configured? which client ID?
    2. POST  /auth/google    {credential} from Google Identity Services
                             -> app session token + account
    3. POST  /auth/register  complete the profile: username, MLBB ID and the
                             app password (needs the session token)
    4. GET   /auth/me        the signed-in account
    5. PATCH /auth/me        change the profile (confirmed by the app password)
    6. POST  /auth/logout    forget the session

Google is the only credential. The MLBB ID is **self-declared**: it is stored
as typed, never checked against Moonton, and the API says so on every response.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.v1.deps import get_auth_service
from app.core.config import get_settings
from app.core.errors import AuthRequiredError
from app.db.models import User
from app.schemas.auth import (
    AuthConfig,
    AuthSession,
    GoogleSignInRequest,
    RegisterRequest,
    UpdateProfileRequest,
    UserAccount,
)
from app.schemas.common import ItemResponse, Meta
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

_bearer = HTTPBearer(
    auto_error=False,
    description="App session token from POST /api/v1/auth/google",
)

_MLBB_ID_NOTE = "MLBB ID is self-declared by the player and is not verified."


def get_account_token(
    creds: Annotated[HTTPAuthorizationCredentials | None, Security(_bearer)],
) -> str:
    if creds is None or not creds.credentials:
        raise AuthRequiredError("Sign in with Google to continue.")
    return creds.credentials


AccountToken = Annotated[str, Depends(get_account_token)]


def get_current_user(
    token: AccountToken,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    return service.require_user(token)


CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get(
    "/config",
    response_model=ItemResponse[AuthConfig],
    summary="Sign-in configuration for the client",
)
async def auth_config() -> ItemResponse[AuthConfig]:
    """Tell the app whether Google sign-in is usable on this deployment.

    The client ID is public (it ships to the browser), so exposing it is safe;
    an empty one means sign-in is not configured and the app says so.
    """
    settings = get_settings()
    enabled = bool(settings.google_client_id)
    return ItemResponse(
        data=AuthConfig(
            google_sign_in_enabled=enabled,
            google_client_id=settings.google_client_id or None,
        ),
        meta=Meta(
            note=(
                "Google is the only sign-in method."
                if enabled
                else "Google sign-in is not configured on this server."
            )
        ),
    )


@router.post(
    "/google",
    response_model=ItemResponse[AuthSession],
    summary="Sign in with a Google ID token",
    responses={
        401: {"description": "The Google token could not be verified"},
        503: {"description": "Google sign-in is not configured on this server"},
    },
)
async def google_sign_in(
    payload: GoogleSignInRequest,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> ItemResponse[AuthSession]:
    result = await service.sign_in_with_google(payload.credential)
    return ItemResponse(
        data=AuthSession(
            session_token=result.session_token,
            user=UserAccount.from_user(result.user),
            is_new_user=result.is_new_user,
        ),
        meta=Meta(),
    )


@router.post(
    "/register",
    response_model=ItemResponse[UserAccount],
    summary="Set the username, MLBB ID and app password",
    responses={409: {"description": "Username taken or profile already set up"}},
)
def register(
    payload: RegisterRequest,
    token: AccountToken,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> ItemResponse[UserAccount]:
    """Complete a freshly created account.

    The password is app-only: hashed with scrypt and never sent to Moonton. It
    is not a sign-in method - Google is.
    """
    user = service.register(
        token,
        username=payload.username,
        mlbb_id=payload.mlbb_id,
        password=payload.password,
    )
    return ItemResponse(
        data=UserAccount.from_user(user),
        meta=Meta(note=_MLBB_ID_NOTE),
    )


@router.get(
    "/me",
    response_model=ItemResponse[UserAccount],
    summary="The signed-in account",
    responses={401: {"description": "Missing, unknown or expired session"}},
)
def me(user: CurrentUser) -> ItemResponse[UserAccount]:
    return ItemResponse(
        data=UserAccount.from_user(user),
        meta=Meta(note=_MLBB_ID_NOTE),
    )


@router.patch(
    "/me",
    response_model=ItemResponse[UserAccount],
    summary="Change the profile (confirmed by the app password)",
    responses={
        403: {"description": "The app password did not match"},
        409: {"description": "Username taken"},
    },
)
def update_me(
    payload: UpdateProfileRequest,
    token: AccountToken,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> ItemResponse[UserAccount]:
    user = service.update_profile(
        token,
        username=payload.username,
        mlbb_id=payload.mlbb_id,
        current_password=payload.current_password,
        new_password=payload.new_password,
    )
    return ItemResponse(
        data=UserAccount.from_user(user),
        meta=Meta(note=_MLBB_ID_NOTE),
    )


@router.post("/logout", summary="Forget this app session")
def logout(
    token: AccountToken,
    service: Annotated[AuthService, Depends(get_auth_service)],
) -> ItemResponse[dict]:
    service.sign_out(token)
    return ItemResponse(data={"signedOut": True}, meta=Meta())
