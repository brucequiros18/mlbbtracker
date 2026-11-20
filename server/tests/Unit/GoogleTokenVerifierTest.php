<?php

namespace Tests\Unit;

use App\Exceptions\ApiException;
use App\Services\GoogleTokenVerifier;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Http;
use Tests\Concerns\SignsJwtTokens;
use Tests\TestCase;

/**
 * The real Google ID token verification path, offline.
 *
 * Tokens are signed with a committed test RSA key and Http::fake serves a
 * JWKS built from the same key - so the signature check, claim validation,
 * key-rotation refetch, caching and outage handling all run for real.
 */
class GoogleTokenVerifierTest extends TestCase
{
    use SignsJwtTokens;

    private const CLIENT_ID = 'test-client-id';

    private const KEY_ID = 'test-key-1';

    private GoogleTokenVerifier $verifier;

    protected function setUp(): void
    {
        parent::setUp();

        // The array cache store persists for the whole test process; the
        // verifier's JWKS cache must never leak between cases.
        Cache::clear();

        $this->verifier = new GoogleTokenVerifier(self::CLIENT_ID);

        // Each test stubs exactly what it needs; anything else is a bug.
        Http::preventStrayRequests();
    }

    public function test_a_valid_token_returns_the_identity(): void
    {
        $this->fakeJwks();
        $token = $this->signToken($this->googleClaims(), self::KEY_ID, $this->staticKey());

        $identity = $this->verifier->verify($token);

        $this->assertSame('google-sub-123', $identity['subject']);
        $this->assertSame('player@example.com', $identity['email']);
        $this->assertTrue($identity['email_verified']);
        $this->assertSame('Player', $identity['name']);
    }

    public function test_a_second_valid_token_is_served_from_the_cached_jwks(): void
    {
        $this->fakeJwks();
        $this->verifier->verify($this->signToken($this->googleClaims(), self::KEY_ID, $this->staticKey()));
        $this->verifier->verify($this->signToken($this->googleClaims(), self::KEY_ID, $this->staticKey()));

        // One key fetch serves both tokens.
        Http::assertSentCount(1);
    }

    public function test_an_unknown_key_id_refetches_then_rejects(): void
    {
        $this->fakeJwks();
        $this->verifier->verify($this->signToken($this->googleClaims(), self::KEY_ID, $this->staticKey()));

        $this->assertRejects(
            fn () => $this->verifier->verify($this->signToken($this->googleClaims(), 'rotated-key', $this->staticKey())),
            401,
            'GOOGLE_TOKEN_INVALID',
        );

        // The known token's fetch, plus two forced refetches for the unknown
        // kid - keyFor retries once more to ride out a mid-rotation window.
        Http::assertSentCount(3);
    }

    public function test_a_token_signed_by_another_key_is_rejected(): void
    {
        $this->fakeJwks();

        // Header claims the listed kid, but the signature is the impostor's.
        $this->assertRejects(
            fn () => $this->verifier->verify($this->signToken($this->googleClaims(), self::KEY_ID, $this->impostorKey())),
            401,
            'GOOGLE_TOKEN_INVALID',
        );
    }

    public function test_a_wrong_issuer_is_rejected(): void
    {
        $this->fakeJwks();
        $token = $this->signToken($this->googleClaims(['iss' => 'https://evil.example']), self::KEY_ID, $this->staticKey());

        $this->assertRejects(fn () => $this->verifier->verify($token), 401, 'GOOGLE_TOKEN_INVALID');
    }

    public function test_a_wrong_audience_is_rejected(): void
    {
        $this->fakeJwks();
        $token = $this->signToken($this->googleClaims(['aud' => 'someone-elses-client']), self::KEY_ID, $this->staticKey());

        $this->assertRejects(fn () => $this->verifier->verify($token), 401, 'GOOGLE_TOKEN_INVALID');
    }

    public function test_an_expired_token_is_rejected(): void
    {
        $this->fakeJwks();
        $token = $this->signToken($this->googleClaims(['exp' => time() - 10]), self::KEY_ID, $this->staticKey());

        $this->assertRejects(fn () => $this->verifier->verify($token), 401, 'GOOGLE_TOKEN_INVALID');
    }

    public function test_an_unverified_email_is_rejected(): void
    {
        $this->fakeJwks();
        $token = $this->signToken($this->googleClaims(['email_verified' => false]), self::KEY_ID, $this->staticKey());

        $this->assertRejects(fn () => $this->verifier->verify($token), 401, 'GOOGLE_TOKEN_INVALID');
    }

    public function test_a_missing_email_is_rejected(): void
    {
        $this->fakeJwks();
        $claims = $this->googleClaims();
        unset($claims['email']);
        $token = $this->signToken($claims, self::KEY_ID, $this->staticKey());

        $this->assertRejects(fn () => $this->verifier->verify($token), 401, 'GOOGLE_TOKEN_INVALID');
    }

    public function test_a_missing_subject_is_rejected(): void
    {
        $this->fakeJwks();
        $claims = $this->googleClaims();
        unset($claims['sub']);
        $token = $this->signToken($claims, self::KEY_ID, $this->staticKey());

        $this->assertRejects(fn () => $this->verifier->verify($token), 401, 'GOOGLE_TOKEN_INVALID');
    }

    public function test_an_hs256_token_is_rejected(): void
    {
        $this->fakeJwks();

        $header = $this->b64url((string) json_encode(['alg' => 'HS256', 'typ' => 'JWT']));
        $payload = $this->b64url((string) json_encode($this->googleClaims()));
        $forged = $header.'.'.$payload.'.'.$this->b64url(hash_hmac('sha256', $header.'.'.$payload, 'secret', true));

        $this->assertRejects(fn () => $this->verifier->verify($forged), 401, 'GOOGLE_TOKEN_INVALID');
    }

    public function test_garbage_input_is_rejected(): void
    {
        $this->assertRejects(fn () => $this->verifier->verify('not-a-jwt'), 401, 'GOOGLE_TOKEN_INVALID');
        $this->assertRejects(fn () => $this->verifier->verify('a.b'), 401, 'GOOGLE_TOKEN_INVALID');
    }

    public function test_a_jwks_outage_is_a_503_not_a_fake_success(): void
    {
        Http::fake([
            GoogleTokenVerifier::JWKS_URL => Http::response('upstream down', 500),
            '*' => Http::response('unexpected outbound call', 500),
        ]);

        // A structurally valid token: the failure must come from the fetch,
        // not from parsing.
        $token = $this->signToken($this->googleClaims(), self::KEY_ID, $this->staticKey());

        $this->assertRejects(
            fn () => $this->verifier->verify($token),
            503,
            'PROVIDER_UNAVAILABLE',
        );
    }

    private function fakeJwks(): void
    {
        Http::fake([
            GoogleTokenVerifier::JWKS_URL => Http::response($this->jwksFor(self::KEY_ID)),
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
