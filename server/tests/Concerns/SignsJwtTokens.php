<?php

namespace Tests\Concerns;

use OpenSSLAsymmetricKey;

/**
 * Sign real RS256 JWTs with a fixed, committed test RSA key.
 *
 * The verifier tests never talk to Google: Http::fake serves a JWKS / X509
 * certificate set built from the same key, so the full verification path
 * (base64url decoding, signature, claim checks) runs for real.
 *
 * The keypair is static (tests/Support/*.pem) because `openssl_pkey_new` and
 * `openssl_csr_new` need a valid OPENSSL_CONF at runtime, which many Windows
 * machines - including CI - cannot guarantee. The key is test-only: it signs
 * nothing real and is never shipped anywhere.
 */
trait SignsJwtTokens
{
    private ?OpenSSLAsymmetricKey $testPrivateKey = null;

    private ?OpenSSLAsymmetricKey $impostorPrivateKey = null;

    private function staticKey(): OpenSSLAsymmetricKey
    {
        if ($this->testPrivateKey instanceof OpenSSLAsymmetricKey) {
            return $this->testPrivateKey;
        }

        $privateKey = openssl_pkey_get_private((string) file_get_contents(dirname(__DIR__).'/Support/private.pem'));
        $this->assertNotFalse($privateKey);

        return $this->testPrivateKey = $privateKey;
    }

    /**
     * A key that is never published in the JWKS / certificates: signs forged
     * tokens in the wrong-signature tests.
     */
    private function impostorKey(): OpenSSLAsymmetricKey
    {
        if ($this->impostorPrivateKey instanceof OpenSSLAsymmetricKey) {
            return $this->impostorPrivateKey;
        }

        $privateKey = openssl_pkey_get_private((string) file_get_contents(dirname(__DIR__).'/Support/impostor.pem'));
        $this->assertNotFalse($privateKey);

        return $this->impostorPrivateKey = $privateKey;
    }

    private function b64url(string $bytes): string
    {
        return rtrim(strtr(base64_encode($bytes), '+/', '-_'), '=');
    }

    /**
     * @param  array<string, mixed>  $claims
     */
    private function signToken(array $claims, string $kid, OpenSSLAsymmetricKey $privateKey): string
    {
        $header = ['alg' => 'RS256', 'typ' => 'JWT', 'kid' => $kid];

        $parts = [
            $this->b64url((string) json_encode($header)),
            $this->b64url((string) json_encode($claims)),
        ];

        openssl_sign(implode('.', $parts), $signature, $privateKey, OPENSSL_ALGO_SHA256);
        $this->assertNotFalse($signature);

        $parts[] = $this->b64url((string) $signature);

        return implode('.', $parts);
    }

    /**
     * A Google-shaped JWKS holding the static key under the given id.
     *
     * @return array<string, mixed>
     */
    private function jwksFor(string $kid): array
    {
        $details = openssl_pkey_get_details($this->staticKey());
        $this->assertNotFalse($details);
        $this->assertArrayHasKey('rsa', $details);

        return [
            'keys' => [
                [
                    'kty' => 'RSA',
                    'alg' => 'RS256',
                    'use' => 'sig',
                    'kid' => $kid,
                    'n' => $this->b64url((string) $details['rsa']['n']),
                    'e' => $this->b64url((string) $details['rsa']['e']),
                ],
            ],
        ];
    }

    /**
     * A Firebase-shaped kid -> PEM certificate map for the static key.
     *
     * @return array<string, string>
     */
    private function certsFor(string $kid): array
    {
        $pem = (string) file_get_contents(dirname(__DIR__).'/Support/certificate.pem');

        return [$kid => $pem];
    }

    /**
     * @param  array<string, mixed>  $overrides
     * @return array<string, mixed>
     */
    private function googleClaims(array $overrides = []): array
    {
        return array_merge([
            'iss' => 'https://accounts.google.com',
            'aud' => 'test-client-id',
            'sub' => 'google-sub-123',
            'email' => 'player@example.com',
            'email_verified' => true,
            'name' => 'Player',
            'iat' => time() - 60,
            'exp' => time() + 3300,
        ], $overrides);
    }

    /**
     * @param  array<string, mixed>  $overrides
     * @return array<string, mixed>
     */
    private function firebaseClaims(array $overrides = []): array
    {
        return array_merge([
            'iss' => 'https://securetoken.google.com/test-project',
            'aud' => 'test-project',
            'sub' => 'firebase-uid-123',
            'email' => 'player@example.com',
            'email_verified' => false,
            'auth_time' => time() - 60,
            'iat' => time() - 60,
            'exp' => time() + 3300,
        ], $overrides);
    }
}
