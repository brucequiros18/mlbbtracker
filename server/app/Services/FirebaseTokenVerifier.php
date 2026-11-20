<?php

namespace App\Services;

use App\Exceptions\ApiException;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

/**
 * Verification of Firebase Authentication ID tokens (email + password).
 *
 * The web app signs the player in with the Firebase JS SDK and sends the
 * resulting ID token to `POST /api/v1/auth/firebase`. This verifier checks it
 * locally, exactly like the Google verifier:
 *
 * - the RS256 signature against Firebase's published X509 certificates,
 * - the issuer (`https://securetoken.google.com/<project-id>`),
 * - the audience (our Firebase project ID),
 * - the expiry and issued-at time,
 * - a non-empty `sub` (the stable Firebase UID, the account key), and
 * - a non-empty email (email/password accounts always carry one).
 *
 * `email_verified` is recorded but not required: a freshly registered
 * Firebase account is unverified until the player clicks the email link, and
 * blocking sign-in on it would lock new players out. The flag is stored so
 * the app can surface a "verify your email" prompt honestly.
 *
 * Only after every check does the caller trust `sub`. The token is never
 * stored.
 */
class FirebaseTokenVerifier
{
    public const CERTS_URL = 'https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com';

    private const CERTS_TTL_SECONDS = 3600;

    /** Clock skew tolerated between the token's iat and this server. */
    private const CLOCK_SKEW_SECONDS = 300;

    private string $projectId;

    public function __construct(string $projectId)
    {
        $this->projectId = $projectId;
    }

    /**
     * @return array{subject: string, email: string, email_verified: bool, name: ?string, picture: ?string}
     */
    public function verify(string $idToken): array
    {
        $parts = explode('.', $idToken);

        if (count($parts) !== 3) {
            throw ApiException::googleTokenInvalid(
                'That Firebase sign-in response could not be read. Please try again.'
            );
        }

        [$headerPart, $payloadPart, $signaturePart] = $parts;
        $header = json_decode($this->base64UrlDecode($headerPart), true);
        $claims = json_decode($this->base64UrlDecode($payloadPart), true);

        if (! is_array($header) || ! is_array($claims)) {
            throw ApiException::googleTokenInvalid(
                'That Firebase sign-in response could not be read. Please try again.'
            );
        }

        if (($header['alg'] ?? null) !== 'RS256' || empty($header['kid'])) {
            throw ApiException::googleTokenInvalid(
                'That Firebase sign-in response used an unsupported signature.'
            );
        }

        $key = $this->keyFor((string) $header['kid']);

        if ($key === null) {
            throw ApiException::googleTokenInvalid(
                'Firebase sign-in could not be verified (unknown signing key).'
            );
        }

        $signature = $this->base64UrlDecode($signaturePart);
        $verified = openssl_verify(
            $headerPart.'.'.$payloadPart,
            $signature,
            $key,
            OPENSSL_ALGO_SHA256
        );

        if ($verified !== 1) {
            Log::info('firebase id token rejected: bad signature');
            throw ApiException::googleTokenInvalid(
                'Firebase sign-in could not be verified. Please sign in again.'
            );
        }

        $this->assertClaims($claims);

        return [
            'subject' => (string) $claims['sub'],
            'email' => (string) $claims['email'],
            // Fresh email/password accounts are unverified until the player
            // clicks Firebase's email link; the flag is stored, not enforced.
            'email_verified' => $claims['email_verified'] === true,
            'name' => isset($claims['name']) && is_string($claims['name']) ? $claims['name'] : null,
            'picture' => isset($claims['picture']) && is_string($claims['picture']) ? $claims['picture'] : null,
        ];
    }

    /**
     * @param  array<string, mixed>  $claims
     */
    private function assertClaims(array $claims): void
    {
        foreach (['exp', 'iat', 'aud', 'iss', 'sub'] as $required) {
            if (! array_key_exists($required, $claims)) {
                throw ApiException::googleTokenInvalid(
                    'Firebase sign-in could not be verified. Please sign in again.'
                );
            }
        }

        if ((string) $claims['iss'] !== 'https://securetoken.google.com/'.$this->projectId) {
            throw ApiException::googleTokenInvalid(
                'Firebase sign-in could not be verified. Please sign in again.'
            );
        }

        if ((string) $claims['aud'] !== $this->projectId) {
            throw ApiException::googleTokenInvalid(
                'Firebase sign-in could not be verified. Please sign in again.'
            );
        }

        $now = time();

        if ((int) $claims['exp'] <= $now) {
            throw ApiException::googleTokenInvalid(
                'That Firebase sign-in response has expired. Please sign in again.'
            );
        }

        if ((int) $claims['iat'] > $now + self::CLOCK_SKEW_SECONDS) {
            throw ApiException::googleTokenInvalid(
                'That Firebase sign-in response is not valid yet. Please sign in again.'
            );
        }

        if (! is_string($claims['sub']) || $claims['sub'] === '') {
            throw ApiException::googleTokenInvalid('The Firebase account has no stable identifier.');
        }

        if (! is_string($claims['email'] ?? null) || $claims['email'] === '') {
            throw ApiException::googleTokenInvalid(
                'Firebase did not share an email address for this account.'
            );
        }
    }

    /**
     * The PEM public key for a key id, or null when Firebase does not know it.
     */
    private function keyFor(string $keyId): ?string
    {
        $certs = $this->certs();

        if (! isset($certs[$keyId])) {
            // Firebase rotates its keys: refetch once before rejecting.
            $certs = $this->certs(forceRefresh: true);
        }

        if (! isset($certs[$keyId])) {
            return null;
        }

        // The JWKS here is a map of kid -> PEM certificate. Extract the
        // contained public key for openssl_verify.
        $certificate = @openssl_x509_read((string) $certs[$keyId]);

        if ($certificate === false) {
            return null;
        }

        $publicKey = openssl_pkey_get_public($certificate);

        return $publicKey === false ? null : $publicKey;
    }

    /**
     * @return array<string, string>
     */
    private function certs(bool $forceRefresh = false): array
    {
        $cacheKey = 'firebase:certs';

        if (! $forceRefresh) {
            $cached = Cache::get($cacheKey);
            if (is_array($cached)) {
                return $cached;
            }
        }

        try {
            $response = Http::withHeaders([
                'accept' => 'application/json',
            ])
                ->timeout((float) config('mlbb.http_timeout'))
                ->get(self::CERTS_URL);

            if (! $response->successful()) {
                throw ApiException::providerUnavailable(
                    'Could not reach Firebase to verify the sign-in. Please try again.'
                );
            }

            $payload = $response->json();
        } catch (ApiException $exception) {
            throw $exception;
        } catch (\Throwable $exception) {
            Log::warning('could not fetch Firebase certificates: '.$exception->getMessage());

            throw ApiException::providerUnavailable(
                'Could not reach Firebase to verify the sign-in. Please try again.'
            );
        }

        $certs = [];

        foreach (is_array($payload) ? $payload : [] as $kid => $certificate) {
            if (is_string($kid) && is_string($certificate)) {
                $certs[$kid] = $certificate;
            }
        }

        Cache::put($cacheKey, $certs, self::CERTS_TTL_SECONDS);

        return $certs;
    }

    private function base64UrlDecode(string $value): string
    {
        $remainder = strlen($value) % 4;
        if ($remainder !== 0) {
            $value .= str_repeat('=', 4 - $remainder);
        }

        $decoded = base64_decode(strtr($value, '-_', '+/'), true);

        return $decoded === false ? '' : $decoded;
    }
}
