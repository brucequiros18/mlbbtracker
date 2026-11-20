<?php

namespace Tests\Fakes;

use App\Exceptions\ApiException;
use App\Services\FirebaseTokenVerifier;

/**
 * A Firebase verifier that never talks to Firebase.
 *
 * The real verifier (signature, issuer, audience, expiry) is covered by its
 * own logic; here only the application flow matters.
 */
class FakeFirebaseTokenVerifier extends FirebaseTokenVerifier
{
    /**
     * @var list<string>
     */
    public array $calls = [];

    public function __construct(private readonly string $acceptedToken = 'good-firebase-token-0123456789abcdef')
    {
        parent::__construct('test-firebase-project');
    }

    /**
     * @return array{subject: string, email: string, email_verified: bool, name: ?string, picture: ?string}
     */
    public function verify(string $idToken): array
    {
        $this->calls[] = $idToken;

        if ($idToken !== $this->acceptedToken) {
            throw ApiException::googleTokenInvalid(
                'Firebase sign-in could not be verified. Please sign in again.'
            );
        }

        return [
            // Email/password accounts have no display name or picture.
            'subject' => 'firebase-uid-1',
            'email' => 'ash@example.com',
            'email_verified' => false,
            'name' => null,
            'picture' => null,
        ];
    }
}
