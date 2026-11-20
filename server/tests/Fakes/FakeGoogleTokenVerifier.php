<?php

namespace Tests\Fakes;

use App\Exceptions\ApiException;
use App\Services\GoogleTokenVerifier;

/**
 * A Google verifier that never talks to Google.
 *
 * The real verifier (signature, issuer, audience, expiry) is covered by its
 * own test; here only the application flow matters.
 */
class FakeGoogleTokenVerifier extends GoogleTokenVerifier
{
    /**
     * @var list<string>
     */
    public array $calls = [];

    public function __construct(private readonly string $acceptedCredential = 'good-google-token-0123456789abcdef')
    {
        parent::__construct('test-client.apps.googleusercontent.com');
    }

    /**
     * @return array{subject: string, email: string, email_verified: bool, name: ?string, picture: ?string}
     */
    public function verify(string $credential): array
    {
        $this->calls[] = $credential;

        if ($credential !== $this->acceptedCredential) {
            throw ApiException::googleTokenInvalid(
                'Google sign-in could not be verified. Please sign in again.'
            );
        }

        return [
            'subject' => 'google-sub-1',
            'email' => 'ash@example.com',
            'email_verified' => true,
            'name' => 'Ash',
            'picture' => 'https://img.example/ash.png',
        ];
    }
}
