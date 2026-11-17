"""Typed application errors with a single JSON error envelope.

Every failure is returned as::

    {"status": "error", "code": "...", "message": "...", "timestamp": "..."}

so the Flutter client can branch on a stable ``code`` instead of parsing
free-form text.
"""

from __future__ import annotations

from datetime import datetime, timezone


class AppError(Exception):
    status_code = 500
    code = "INTERNAL_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def to_payload(self) -> dict[str, str]:
        return {
            "status": "error",
            "code": self.code,
            "message": self.message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"


class ValidationAppError(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"


class ProviderError(AppError):
    """A provider returned an error or an unusable payload."""

    status_code = 502
    code = "PROVIDER_ERROR"


class ProviderUnavailableError(AppError):
    status_code = 503
    code = "PROVIDER_UNAVAILABLE"


class ProviderAuthError(AppError):
    status_code = 401
    code = "PROVIDER_AUTH_REQUIRED"


class AuthRequiredError(AppError):
    """The request needs a signed-in MLBB Tracker account (Google sign-in)."""

    status_code = 401
    code = "AUTH_REQUIRED"


class GoogleNotConfiguredError(AppError):
    """Google sign-in is not configured on this server (no OAuth client ID)."""

    status_code = 503
    code = "GOOGLE_NOT_CONFIGURED"


class GoogleTokenInvalidError(AppError):
    """The Google ID token could not be verified."""

    status_code = 401
    code = "GOOGLE_TOKEN_INVALID"


class UsernameTakenError(AppError):
    status_code = 409
    code = "USERNAME_TAKEN"


class ProfileAlreadyCompleteError(AppError):
    """Registration was attempted for an account that already has a profile."""

    status_code = 409
    code = "PROFILE_ALREADY_COMPLETE"


class InvalidPasswordError(AppError):
    """The app password did not match the stored hash.

    403, not 401: the bearer session is valid, the confirmation failed.
    """

    status_code = 403
    code = "INVALID_PASSWORD"


class NotSupportedError(AppError):
    """The requested capability has no permitted data source."""

    status_code = 501
    code = "NOT_SUPPORTED"

    def __init__(self, message: str, details: str | None = None) -> None:
        super().__init__(message)
        self.details = details

    def to_payload(self) -> dict[str, str]:
        payload = super().to_payload()
        if self.details:
            payload["details"] = self.details
        return payload
