<?php

namespace App\Exceptions;

use Exception;
use Illuminate\Http\JsonResponse;
use Throwable;

/**
 * Typed application error with a single JSON error envelope.
 *
 * Every failure is returned as::
 *
 *     {"status": "error", "code": "...", "message": "...", "timestamp": "..."}
 *
 * so clients can branch on a stable `code` instead of parsing free-form text.
 */
class ApiException extends Exception
{
    /**
     * @param  string|null  $details  Extra context about the failure.
     */
    public function __construct(
        string $message,
        protected int $statusCode = 500,
        protected string $errorCode = 'INTERNAL_ERROR',
        protected ?string $details = null,
        ?Throwable $previous = null,
    ) {
        parent::__construct($message, 0, $previous);
    }

    public static function notFound(string $message): self
    {
        return new self($message, 404, 'NOT_FOUND');
    }

    public static function validation(string $message, ?array $details = null): self
    {
        return new self(
            $message,
            422,
            'VALIDATION_ERROR',
            $details === null ? null : (string) json_encode($details)
        );
    }

    public static function providerError(string $message): self
    {
        return new self($message, 502, 'PROVIDER_ERROR');
    }

    public static function providerUnavailable(string $message): self
    {
        return new self($message, 503, 'PROVIDER_UNAVAILABLE');
    }

    public static function providerAuth(string $message): self
    {
        return new self($message, 401, 'PROVIDER_AUTH_REQUIRED');
    }

    public static function authRequired(string $message = 'Sign in with Google to continue.'): self
    {
        return new self($message, 401, 'AUTH_REQUIRED');
    }

    public static function googleNotConfigured(string $message): self
    {
        return new self($message, 503, 'GOOGLE_NOT_CONFIGURED');
    }

    public static function googleTokenInvalid(string $message): self
    {
        return new self($message, 401, 'GOOGLE_TOKEN_INVALID');
    }

    public static function usernameTaken(string $message): self
    {
        return new self($message, 409, 'USERNAME_TAKEN');
    }

    public static function profileAlreadyComplete(string $message): self
    {
        return new self($message, 409, 'PROFILE_ALREADY_COMPLETE');
    }

    public static function invalidPassword(string $message): self
    {
        return new self($message, 403, 'INVALID_PASSWORD');
    }

    public static function notSupported(string $message, ?string $details = null): self
    {
        return new self($message, 501, 'NOT_SUPPORTED', $details);
    }

    /**
     * @return array<string, mixed>
     */
    public function payload(): array
    {
        $payload = [
            'status' => 'error',
            'code' => $this->errorCode,
            'message' => $this->getMessage(),
            'timestamp' => now()->utc()->format('Y-m-d\TH:i:s.u\Z'),
        ];

        if ($this->details !== null) {
            $payload['details'] = $this->details;
        }

        return $payload;
    }

    public function statusCode(): int
    {
        return $this->statusCode;
    }

    public function errorCode(): string
    {
        return $this->errorCode;
    }

    public function render(): JsonResponse
    {
        return response()->json($this->payload(), $this->statusCode);
    }
}
