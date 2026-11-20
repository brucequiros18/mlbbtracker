<?php

namespace App\Services;

use App\Exceptions\ApiException;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

/**
 * Verification of Google ID tokens.
 *
 * The web app signs in with Google Identity Services and sends the resulting
 * ID token to `POST /api/v1/auth/google`. This verifier checks it locally:
 *
 * - the signature against Google's published JWKS (RS256),
 * - the issuer (`accounts.google.com`),
 * - the audience (our own OAuth client ID),
 * - the expiry, and
 * - that the Google account's email is verified.
 *
 * Only then does it trust the `sub` claim, which is Google's stable subject
 * ID and the identity key of an account. The token is never stored.
 */
class GoogleTokenVerifier
{
    public const JWKS_URL = 'https://www.googleapis.com/oauth2/v3/certs';

    /**
     * @var list<string>
     */
    public const ISSUERS = ['https://accounts.google.com', 'accounts.google.com'];

    private const JWKS_TTL_SECONDS = 300;

    private string $clientId;

    public function __construct(string $clientId)
    {
        $this->clientId = $clientId;
    }

    /**
     * @return array{subject: string, email: string, email_verified: bool, name: ?string, picture: ?string}
     */
    public function verify(string $credential): array
    {
        $parts = explode('.', $credential);

        if (count($parts) !== 3) {
            throw ApiException::googleTokenInvalid(
                'That Google sign-in response could not be read. Please try again.'
            );
        }

        [$headerPart, $payloadPart, $signaturePart] = $parts;
        $header = json_decode($this->base64UrlDecode($headerPart), true);
        $claims = json_decode($this->base64UrlDecode($payloadPart), true);

        if (! is_array($header) || ! is_array($claims)) {
            throw ApiException::googleTokenInvalid(
                'That Google sign-in response could not be read. Please try again.'
            );
        }

        if (($header['alg'] ?? null) !== 'RS256' || empty($header['kid'])) {
            throw ApiException::googleTokenInvalid(
                'That Google sign-in response used an unsupported signature.'
            );
        }

        $key = $this->keyFor((string) $header['kid']);

        if ($key === null) {
            throw ApiException::googleTokenInvalid(
                'Google sign-in could not be verified (unknown signing key).'
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
            Log::info('google id token rejected: bad signature');
            throw ApiException::googleTokenInvalid(
                'Google sign-in could not be verified. Please sign in again.'
            );
        }

        $this->assertClaims($claims);

        return [
            'subject' => (string) $claims['sub'],
            'email' => (string) $claims['email'],
            'email_verified' => true,
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
                    'Google sign-in could not be verified. Please sign in again.'
                );
            }
        }

        if (! in_array((string) $claims['iss'], self::ISSUERS, true)) {
            throw ApiException::googleTokenInvalid(
                'Google sign-in could not be verified. Please sign in again.'
            );
        }

        $audience = $claims['aud'];
        $audiences = is_array($audience) ? $audience : [$audience];

        if (! in_array($this->clientId, array_map('strval', $audiences), true)) {
            throw ApiException::googleTokenInvalid(
                'Google sign-in could not be verified. Please sign in again.'
            );
        }

        if ((int) $claims['exp'] <= time()) {
            throw ApiException::googleTokenInvalid(
                'That Google sign-in response has expired. Please sign in again.'
            );
        }

        if (! is_string($claims['sub']) || $claims['sub'] === '') {
            throw ApiException::googleTokenInvalid('The Google account has no stable identifier.');
        }

        if (! is_string($claims['email'] ?? null) || $claims['email'] === '') {
            throw ApiException::googleTokenInvalid(
                'Google did not share an email address for this account.'
            );
        }

        if (! $this->isEmailVerified($claims['email_verified'] ?? null)) {
            throw ApiException::googleTokenInvalid(
                'Your Google email address is not verified, so it cannot be used to sign in.'
            );
        }
    }

    private function isEmailVerified(mixed $value): bool
    {
        if (is_bool($value)) {
            return $value;
        }

        if (is_string($value)) {
            return strtolower(trim($value)) === 'true';
        }

        return false;
    }

    /**
     * The PEM public key for a key id, or null when Google does not know it.
     */
    private function keyFor(string $keyId): ?string
    {
        $keys = $this->jwks();

        if (! isset($keys[$keyId])) {
            // Google rotates its keys: refetch once before rejecting the token.
            $keys = $this->jwks(forceRefresh: true);
        }

        if (! isset($keys[$keyId])) {
            // Second refetch attempt: Google may be in the middle of key rotation.
            $keys = $this->jwks(forceRefresh: true);
        }

        if (! isset($keys[$keyId])) {
            return null;
        }

        return $this->pemFromJwk($keys[$keyId]);
    }

    /**
     * @return array<string, array<string, mixed>>
     */
    private function jwks(bool $forceRefresh = false): array
    {
        $cacheKey = 'google:jwks';

        if (! $forceRefresh) {
            $cached = Cache::get($cacheKey);
            if (is_array($cached)) {
                return $cached;
            }
        }

        try {
            $response = Http::withHeaders([
                'user-agent' => (string) config('mlbb.http_user_agent'),
                'accept' => 'application/json',
            ])
                ->timeout((float) config('mlbb.http_timeout'))
                ->get(self::JWKS_URL);

            if (! $response->successful()) {
                throw ApiException::providerUnavailable(
                    'Could not reach Google to verify the sign-in. Please try again.'
                );
            }

            $payload = $response->json();
        } catch (ApiException $exception) {
            throw $exception;
        } catch (\Throwable $exception) {
            Log::warning('could not fetch Google JWKS: '.$exception->getMessage());

            throw ApiException::providerUnavailable(
                'Could not reach Google to verify the sign-in. Please try again.'
            );
        }

        $keys = [];

        foreach (is_array($payload['keys'] ?? null) ? $payload['keys'] : [] as $jwk) {
            if (is_array($jwk) && isset($jwk['kid']) && is_string($jwk['kid'])) {
                $keys[$jwk['kid']] = $jwk;
            }
        }

        Cache::put($cacheKey, $keys, self::JWKS_TTL_SECONDS);

        return $keys;
    }

    /**
     * @param  array<string, mixed>  $jwk
     */
    private function pemFromJwk(array $jwk): ?string
    {
        if (($jwk['kty'] ?? null) !== 'RSA' || ! isset($jwk['n'], $jwk['e'])) {
            return null;
        }

        // The PEM is assembled with a small DER encoder instead of
        // openssl_pkey_new: constructing a public key from raw modulus and
        // exponent components is exactly the OpenSSL call that fails on
        // hosts with a broken OPENSSL_CONF, and the encoding is fully
        // specified so it needs no OpenSSL at all.
        $modulus = $this->base64UrlDecode((string) $jwk['n']);
        $exponent = $this->base64UrlDecode((string) $jwk['e']);

        if ($modulus === '' || $exponent === '') {
            return null;
        }

        $rsaPublicKey = $this->derSequence(
            $this->derInteger($modulus).
            $this->derInteger($exponent)
        );

        // SubjectPublicKeyInfo: SEQUENCE { SEQUENCE { OID rsaEncryption, NULL },
        // BIT STRING { RSAPublicKey } } - rsaEncryption is 1.2.840.113549.1.1.1.
        $subjectPublicKeyInfo = $this->derSequence(
            $this->derSequence($this->derOid("\x2a\x86\x48\x86\xf7\x0d\x01\x01\x01").$this->derNull()).
            $this->derBitString($rsaPublicKey)
        );

        return "-----BEGIN PUBLIC KEY-----\n".
            chunk_split(base64_encode($subjectPublicKeyInfo), 64, "\n").
            '-----END PUBLIC KEY-----';
    }

    private function derSequence(string $content): string
    {
        return $this->derTag(0x30, $content);
    }

    private function derNull(): string
    {
        return "\x05\x00";
    }

    private function derOid(string $encodedOid): string
    {
        return $this->derTag(0x06, $encodedOid);
    }

    private function derBitString(string $bytes): string
    {
        // The first content byte carries the count of unused trailing bits.
        return $this->derTag(0x03, "\x00".$bytes);
    }

    private function derInteger(string $bytes): string
    {
        // DER integers are signed: a positive value with a high first bit
        // needs a leading zero byte.
        $bytes = ltrim($bytes, "\x00");

        if ($bytes === '') {
            $bytes = "\x00";
        } elseif (ord($bytes[0]) >= 0x80) {
            $bytes = "\x00".$bytes;
        }

        return $this->derTag(0x02, $bytes);
    }

    private function derTag(int $tag, string $content): string
    {
        $length = strlen($content);

        if ($length < 0x80) {
            return chr($tag).chr($length).$content;
        }

        $encodedLength = ltrim(pack('N', $length), "\x00");

        return chr($tag).chr(0x80 | strlen($encodedLength)).$encodedLength.$content;
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
