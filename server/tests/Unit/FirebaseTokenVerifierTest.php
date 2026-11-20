<?php

namespace Tests\Unit;

use App\Exceptions\ApiException;
use App\Services\FirebaseTokenVerifier;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Http;
use Tests\Concerns\SignsJwtTokens;
use Tests\TestCase;

/**
 * The real Firebase ID token verification path, offline.
 *
 * Tokens are signed with a committed test RSA key and Http::fake serves a
 * self-signed X509 certificate for the same key - so the certificate parsing,
 * signature check, claim validation, key-rotation refetch, caching and outage
 * handling all run for real.
 */
class FirebaseTokenVerifierTest extends TestCase
{
    use SignsJwtTokens;

    private const PROJECT_ID = 'test-project';

    private const KEY_ID = 'test-firebase-key-1';

    private FirebaseTokenVerifier $verifier;

    protected function setUp(): void
    {
        parent::setUp();

        Cache::clear();

        $this->verifier = new FirebaseTokenVerifier(self::PROJECT_ID);

        // Each test stubs exactly what it needs; anything else is a bug.
        Http::preventStrayRequests();
    }

    public function test_a_valid_token_returns_the_identity(): void
    {
        $this->fakeCerts();
        $token = $this->signToken($this->firebaseClaims(), self::KEY_ID, $this->staticKey());

        $identity = $this->verifier->verify($token);

        $this->assertSame('firebase-uid-123', $identity['subject']);
        $this->assertSame('player@example.com', $identity['email']);
        // Recorded, not enforced: fresh email/password accounts are unverified.
        $this->assertFalse($identity['email_verified']);
        $this->assertNull($identity['name']);
        $this->assertNull($identity['picture']);
    }

    public function test_an_unverified_email_still_signs_in(): void
    {
        $this->fakeCerts();
        $token = $this->signToken($this->firebaseClaims(['email_verified' => false]), self::KEY_ID, $this->staticKey());

        $identity = $this->verifier->verify($token);

        $this->assertFalse($identity['email_verified']);
    }

    public function test_a_second_valid_token_is_served_from_the_cached_certificates(): void
    {
        $this->fakeCerts();
        $this->verifier->verify($this->signToken($this->firebaseClaims(), self::KEY_ID, $this->staticKey()));
        $this->verifier->verify($this->signToken($this->firebaseClaims(), self::KEY_ID, $this->staticKey()));

        Http::assertSentCount(1);
    }

    public function test_an_unknown_key_id_refetches_then_rejects(): void
    {
        $this->fakeCerts();
        $this->verifier->verify($this->signToken($this->firebaseClaims(), self::KEY_ID, $this->staticKey()));

        $this->assertRejects(
            fn () => $this->verifier->verify($this->signToken($this->firebaseClaims(), 'rotated-key', $this->staticKey())),
            401,
            'GOOGLE_TOKEN_INVALID',
        );

        Http::assertSentCount(2);
    }

    public function test_a_token_signed_by_another_key_is_rejected(): void
    {
        $this->fakeCerts();

        $this->assertRejects(
            fn () => $this->verifier->verify($this->signToken($this->firebaseClaims(), self::KEY_ID, $this->impostorKey())),
            401,
            'GOOGLE_TOKEN_INVALID',
        );
    }

    public function test_a_wrong_issuer_is_rejected(): void
    {
        $this->fakeCerts();
        $token = $this->signToken($this->firebaseClaims(['iss' => 'https://securetoken.google.com/other-project']), self::KEY_ID, $this->staticKey());

        $this->assertRejects(fn () => $this->verifier->verify($token), 401, 'GOOGLE_TOKEN_INVALID');
    }

    public function test_a_wrong_audience_is_rejected(): void
    {
        $this->fakeCerts();
        $token = $this->signToken($this->firebaseClaims(['aud' => 'other-project']), self::KEY_ID, $this->staticKey());

        $this->assertRejects(fn () => $this->verifier->verify($token), 401, 'GOOGLE_TOKEN_INVALID');
    }

    public function test_an_expired_token_is_rejected(): void
    {
        $this->fakeCerts();
        $token = $this->signToken($this->firebaseClaims(['exp' => time() - 10]), self::KEY_ID, $this->staticKey());

        $this->assertRejects(fn () => $this->verifier->verify($token), 401, 'GOOGLE_TOKEN_INVALID');
    }

    public function test_a_token_issued_in_the_future_is_rejected(): void
    {
        $this->fakeCerts();
        $token = $this->signToken($this->firebaseClaims(['iat' => time() + 3600]), self::KEY_ID, $this->staticKey());

        $this->assertRejects(fn () => $this->verifier->verify($token), 401, 'GOOGLE_TOKEN_INVALID');
    }

    public function test_a_missing_email_is_rejected(): void
    {
        $this->fakeCerts();
        $claims = $this->firebaseClaims();
        unset($claims['email']);
        $token = $this->signToken($claims, self::KEY_ID, $this->staticKey());

        $this->assertRejects(fn () => $this->verifier->verify($token), 401, 'GOOGLE_TOKEN_INVALID');
    }

    public function test_a_missing_subject_is_rejected(): void
    {
        $this->fakeCerts();
        $claims = $this->firebaseClaims();
        unset($claims['sub']);
        $token = $this->signToken($claims, self::KEY_ID, $this->staticKey());

        $this->assertRejects(fn () => $this->verifier->verify($token), 401, 'GOOGLE_TOKEN_INVALID');
    }

    public function test_an_hs256_token_is_rejected(): void
    {
        $this->fakeCerts();

        $header = $this->b64url((string) json_encode(['alg' => 'HS256', 'typ' => 'JWT']));
        $payload = $this->b64url((string) json_encode($this->firebaseClaims()));
        $forged = $header.'.'.$payload.'.'.$this->b64url(hash_hmac('sha256', $header.'.'.$payload, 'secret', true));

        $this->assertRejects(fn () => $this->verifier->verify($forged), 401, 'GOOGLE_TOKEN_INVALID');
    }

    public function test_garbage_input_is_rejected(): void
    {
        $this->assertRejects(fn () => $this->verifier->verify('garbage'), 401, 'GOOGLE_TOKEN_INVALID');
    }

    public function test_a_certificate_outage_is_a_503_not_a_fake_success(): void
    {
        Http::fake([
            FirebaseTokenVerifier::CERTS_URL => Http::response('upstream down', 500),
            '*' => Http::response('unexpected outbound call', 500),
        ]);

        // A structurally valid token: the failure must come from the fetch,
        // not from parsing.
        $token = $this->signToken($this->firebaseClaims(), self::KEY_ID, $this->staticKey());

        $this->assertRejects(
            fn () => $this->verifier->verify($token),
            503,
            'PROVIDER_UNAVAILABLE',
        );
    }

    private function fakeCerts(): void
    {
        Http::fake([
            FirebaseTokenVerifier::CERTS_URL => Http::response($this->certsFor(self::KEY_ID)),
            '*' => Http::response('unexpected outbound call', 500),
        ]);
    }

    private function assertRejects(callable $attempt, int $statusCode, string $code): void
    {
        try {
            $attempt();
            $this->fail('Expected the token to be rejected.');
        } catch (ApiException $exception) {
            $this->assertSame($statusCode, $exception->statusCode());
            $this->assertSame($code, $exception->errorCode());
        }
    }
}
