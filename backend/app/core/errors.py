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
