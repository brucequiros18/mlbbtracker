<?php

namespace Tests\Feature;

use App\Models\User;
use App\Models\UserSession;
use App\Services\AuthService;
use App\Support\Passwords;
use Illuminate\Foundation\Testing\RefreshDatabase;
use PHPUnit\Framework\Attributes\DataProvider;
use Tests\Fakes\FakeFirebaseTokenVerifier;
use Tests\Fakes\FakeGoogleTokenVerifier;
use Tests\TestCase;

/**
 * App accounts: Google or Firebase sign-in, profile setup and sessions.
 *
 * Everything here is offline: the verifiers are faked, so no token is ever
 * sent to Google or Firebase.
 */
class AuthTest extends TestCase
{
    use RefreshDatabase;

    // Must satisfy the GoogleSignInRequest rule: credential min:20.
    private const GOOD_TOKEN = 'good-google-token-0123456789abcdef';

    // Must satisfy the Firebase idToken rule: min:20.
    private const GOOD_FIREBASE_TOKEN = 'good-firebase-token-0123456789abcdef';

    protected function setUp(): void
    {
        parent::setUp();

        config([
            'mlbb.google_client_id' => 'test-client.apps.googleusercontent.com',
            'mlbb.firebase_project_id' => 'test-firebase-project',
            'mlbb.firebase_api_key' => 'test-api-key',
            'mlbb.firebase_auth_domain' => '',
        ]);
    }

    private function useFakeVerifier(): FakeGoogleTokenVerifier
    {
        $verifier = new FakeGoogleTokenVerifier(self::GOOD_TOKEN);

        $this->app->bind(AuthService::class, fn () => new AuthService($verifier));

        return $verifier;
    }

    private function useFakeFirebaseVerifier(): FakeFirebaseTokenVerifier
    {
        $verifier = new FakeFirebaseTokenVerifier(self::GOOD_FIREBASE_TOKEN);

        $this->app->bind(AuthService::class, fn () => new AuthService(null, $verifier));

        return $verifier;
    }

    private function firebaseSignIn(): string
    {
        $response = $this->postJson('/api/v1/auth/firebase', [
            'idToken' => self::GOOD_FIREBASE_TOKEN,
        ]);

        $response->assertOk();

        return (string) $response->json('data.sessionToken');
    }

    private function signIn(): string
    {
        $response = $this->postJson('/api/v1/auth/google', [
            'credential' => self::GOOD_TOKEN,
        ]);

        $response->assertOk();

        return (string) $response->json('data.sessionToken');
    }

    /**
     * @param  array<string, mixed>  $overrides
     */
    private function register(string $token, array $overrides = [])
    {
        return $this->withHeader('Authorization', 'Bearer '.$token)
            ->postJson('/api/v1/auth/register', array_merge([
                'username' => 'AshKetchum',
                'mlbbId' => '123456789',
                'password' => 'correct horse battery',
            ], $overrides));
    }

    // -- Configuration -------------------------------------------------------

    public function test_config_reports_google_enabled(): void
    {
        $this->useFakeVerifier();

        $response = $this->getJson('/api/v1/auth/config');

        $response->assertOk()
            ->assertJsonPath('data.googleSignInEnabled', true)
            ->assertJsonPath('data.googleClientId', 'test-client.apps.googleusercontent.com')
            ->assertJsonPath('data.minPasswordLength', 8);
    }

    public function test_unconfigured_server_says_so(): void
    {
        config(['mlbb.google_client_id' => '']);

        $this->getJson('/api/v1/auth/config')
            ->assertOk()
            ->assertJsonPath('data.googleSignInEnabled', false)
            ->assertJsonPath('data.googleClientId', null);

        $this->postJson('/api/v1/auth/google', ['credential' => self::GOOD_TOKEN])
            ->assertStatus(503)
            ->assertJsonPath('code', 'GOOGLE_NOT_CONFIGURED');
    }

    // -- Google sign-in ------------------------------------------------------

    public function test_google_sign_in_creates_an_account_without_a_profile(): void
    {
        $this->useFakeVerifier();

        $response = $this->postJson('/api/v1/auth/google', ['credential' => self::GOOD_TOKEN]);

        $response->assertOk()
            ->assertJsonPath('data.isNewUser', true)
            ->assertJsonPath('data.user.email', 'ash@example.com')
            ->assertJsonPath('data.user.googleName', 'Ash')
            ->assertJsonPath('data.user.username', null)
            ->assertJsonPath('data.user.mlbbId', null)
            ->assertJsonPath('data.user.profileComplete', false)
            // Never verified: the MLBB ID is typed in by the player.
            ->assertJsonPath('data.user.mlbbIdVerified', false);

        $this->assertNotEmpty($response->json('data.sessionToken'));
    }

    public function test_google_sign_in_twice_reuses_the_account(): void
    {
        $this->useFakeVerifier();

        $first = $this->postJson('/api/v1/auth/google', ['credential' => self::GOOD_TOKEN]);
        $second = $this->postJson('/api/v1/auth/google', ['credential' => self::GOOD_TOKEN]);

        $first->assertJsonPath('data.isNewUser', true);
        $second->assertJsonPath('data.isNewUser', false);
        $this->assertSame($first->json('data.user.id'), $second->json('data.user.id'));
        $this->assertNotSame($first->json('data.sessionToken'), $second->json('data.sessionToken'));

        $this->assertSame(1, User::query()->count());
        $this->assertSame(2, UserSession::query()->count());
    }

    public function test_google_sign_in_rejects_an_invalid_token(): void
    {
        $this->useFakeVerifier();

        $this->postJson('/api/v1/auth/google', ['credential' => 'bad-google-token-0123456789abcdef'])
            ->assertStatus(401)
            ->assertJsonPath('code', 'GOOGLE_TOKEN_INVALID');

        $this->assertSame(0, User::query()->count());
    }

    // -- Firebase sign-in (email + password) ---------------------------------

    public function test_config_reports_firebase_enabled(): void
    {
        $this->useFakeFirebaseVerifier();

        $this->getJson('/api/v1/auth/config')
            ->assertOk()
            ->assertJsonPath('data.firebaseEnabled', true)
            ->assertJsonPath('data.firebaseProjectId', 'test-firebase-project')
            ->assertJsonPath('data.firebaseAuthDomain', 'test-firebase-project.firebaseapp.com');
    }

    public function test_config_reports_firebase_disabled_when_unconfigured(): void
    {
        config(['mlbb.firebase_project_id' => '']);
        $this->useFakeVerifier();

        $this->getJson('/api/v1/auth/config')
            ->assertOk()
            ->assertJsonPath('data.firebaseEnabled', false)
            ->assertJsonPath('data.firebaseApiKey', null);

        $this->postJson('/api/v1/auth/firebase', ['idToken' => self::GOOD_FIREBASE_TOKEN])
            ->assertStatus(503)
            ->assertJsonPath('code', 'GOOGLE_NOT_CONFIGURED');
    }

    public function test_firebase_sign_up_creates_an_account_without_a_profile(): void
    {
        $this->useFakeFirebaseVerifier();

        $response = $this->postJson('/api/v1/auth/firebase', ['idToken' => self::GOOD_FIREBASE_TOKEN]);

        $response->assertOk()
            ->assertJsonPath('data.isNewUser', true)
            ->assertJsonPath('data.user.email', 'ash@example.com')
            // Email/password accounts have no display name or picture.
            ->assertJsonPath('data.user.googleName', null)
            ->assertJsonPath('data.user.username', null)
            ->assertJsonPath('data.user.mlbbId', null)
            ->assertJsonPath('data.user.profileComplete', false)
            // Never verified: the MLBB ID is typed in by the player.
            ->assertJsonPath('data.user.mlbbIdVerified', false);

        $this->assertNotEmpty($response->json('data.sessionToken'));

        $user = User::query()->firstOrFail();
        $this->assertSame('firebase-uid-1', $user->firebase_uid);
        $this->assertNull($user->google_sub);
    }

    public function test_firebase_sign_in_twice_reuses_the_account(): void
    {
        $this->useFakeFirebaseVerifier();

        $first = $this->postJson('/api/v1/auth/firebase', ['idToken' => self::GOOD_FIREBASE_TOKEN]);
        $second = $this->postJson('/api/v1/auth/firebase', ['idToken' => self::GOOD_FIREBASE_TOKEN]);

        $first->assertJsonPath('data.isNewUser', true);
        $second->assertJsonPath('data.isNewUser', false);
        $this->assertSame($first->json('data.user.id'), $second->json('data.user.id'));
        $this->assertNotSame($first->json('data.sessionToken'), $second->json('data.sessionToken'));

        $this->assertSame(1, User::query()->count());
        $this->assertSame(2, UserSession::query()->count());
    }

    public function test_firebase_sign_in_rejects_an_invalid_token(): void
    {
        $this->useFakeFirebaseVerifier();

        $this->postJson('/api/v1/auth/firebase', ['idToken' => 'bad-firebase-token-0123456789abcdef'])
            ->assertStatus(401)
            ->assertJsonPath('code', 'GOOGLE_TOKEN_INVALID');

        $this->assertSame(0, User::query()->count());
    }

    public function test_firebase_account_completes_the_profile(): void
    {
        $this->useFakeFirebaseVerifier();

        $token = $this->firebaseSignIn();

        $this->register($token)
            ->assertOk()
            ->assertJsonPath('data.username', 'AshKetchum')
            ->assertJsonPath('data.mlbbId', '123456789')
            ->assertJsonPath('data.profileComplete', true);

        // The Firebase account and the app password coexist: Firebase is the
        // sign-in credential, the app password confirms profile edits.
        $user = User::query()->firstOrFail();
        $this->assertNotNull($user->password_hash);
        $this->assertTrue(Passwords::verify('correct horse battery', $user->password_hash));
    }

    // -- Registration --------------------------------------------------------

    public function test_register_completes_the_profile(): void
    {
        $this->useFakeVerifier();

        $token = $this->signIn();

        $this->register($token)
            ->assertOk()
            ->assertJsonPath('data.username', 'AshKetchum')
            ->assertJsonPath('data.mlbbId', '123456789')
            ->assertJsonPath('data.profileComplete', true)
            ->assertJsonPath('data.mlbbIdVerified', false);

        $user = User::query()->firstOrFail();

        // The password is hashed, never stored in plaintext.
        $this->assertNotNull($user->password_hash);
        $this->assertStringNotContainsString('correct horse battery', $user->password_hash);
        $this->assertTrue(Passwords::verify('correct horse battery', $user->password_hash));
    }

    public function test_register_requires_a_session(): void
    {
        $this->useFakeVerifier();

        $this->postJson('/api/v1/auth/register', [
            'username' => 'AshKetchum',
            'mlbbId' => '123456789',
            'password' => 'correct horse battery',
        ])
            ->assertStatus(401)
            ->assertJsonPath('code', 'AUTH_REQUIRED');
    }

    public function test_register_rejects_a_duplicate_username_case_insensitively(): void
    {
        $this->useFakeVerifier();

        $token = $this->signIn();
        $this->register($token)->assertOk();

        // A second Google account picks the same name in a different case.
        User::query()->create([
            'google_sub' => 'google-sub-2',
            'email' => 'misty@example.com',
            'email_verified' => true,
            'google_name' => 'Misty',
        ]);

        $second = User::query()->where('google_sub', 'google-sub-2')->firstOrFail();
        UserSession::query()->create([
            'token_hash' => hash('sha256', 'second-token'),
            'user_id' => $second->id,
            'expires_at' => now()->addDay(),
            'last_seen_at' => now(),
        ]);

        $this->register('second-token', ['username' => 'ashketchum'])
            ->assertStatus(409)
            ->assertJsonPath('code', 'USERNAME_TAKEN');

        // The rejected registration must not have touched the second user's
        // own session (the first user's session from signIn() also exists).
        $this->assertSame(1, UserSession::query()->where('user_id', $second->id)->count());
    }

    public function test_register_rejects_a_second_profile(): void
    {
        $this->useFakeVerifier();

        $token = $this->signIn();
        $this->register($token)->assertOk();

        $this->register($token, ['username' => 'SomeoneElse'])
            ->assertStatus(409)
            ->assertJsonPath('code', 'PROFILE_ALREADY_COMPLETE');
    }

    /**
     * @return array<string, array<string, mixed>>
     */
    public static function invalidProfiles(): array
    {
        // Each data set is wrapped in an outer array so PHPUnit passes it
        // positionally as $overrides instead of as named arguments.
        return [
            'username too short' => [['username' => 'ab']],
            'username with a space' => [['username' => 'has space']],
            'username with a dash' => [['username' => 'Ash-Ketchum']],
            'mlbb id with letters' => [['mlbbId' => '12ab']],
            'mlbb id too short' => [['mlbbId' => '123']],
            'password too short' => [['password' => 'short']],
        ];
    }

    /**
     * @param  array<string, mixed>  $overrides
     */
    #[DataProvider('invalidProfiles')]
    public function test_register_validates_input(array $overrides): void
    {
        $this->useFakeVerifier();

        $token = $this->signIn();

        $this->register($token, $overrides)->assertStatus(422);
    }

    // -- Session -------------------------------------------------------------

    public function test_me_returns_the_account(): void
    {
        $this->useFakeVerifier();

        $token = $this->signIn();

        $this->withHeader('Authorization', 'Bearer '.$token)
            ->getJson('/api/v1/auth/me')
            ->assertOk()
            ->assertJsonPath('data.email', 'ash@example.com');
    }

    public function test_me_rejects_unknown_and_expired_tokens(): void
    {
        $this->useFakeVerifier();

        $this->withHeader('Authorization', 'Bearer nope')
            ->getJson('/api/v1/auth/me')
            ->assertStatus(401)
            ->assertJsonPath('code', 'AUTH_REQUIRED');

        $token = $this->signIn();

        $session = UserSession::query()->firstOrFail();
        $session->expires_at = now()->subMinute();
        $session->save();

        $this->withHeader('Authorization', 'Bearer '.$token)
            ->getJson('/api/v1/auth/me')
            ->assertStatus(401)
            ->assertJsonPath('code', 'AUTH_REQUIRED');
    }

    public function test_logout_forgets_the_session(): void
    {
        $this->useFakeVerifier();

        $token = $this->signIn();
        $headers = ['Authorization' => 'Bearer '.$token];

        $this->withHeaders($headers)->postJson('/api/v1/auth/logout')->assertOk();
        $this->withHeaders($headers)->getJson('/api/v1/auth/me')->assertStatus(401);

        // Only the session row is gone; the account stays.
        $this->assertSame(0, UserSession::query()->count());
        $this->assertSame(1, User::query()->count());
    }

    // -- Profile edits -------------------------------------------------------

    public function test_update_requires_the_app_password(): void
    {
        $this->useFakeVerifier();

        $token = $this->signIn();
        $this->register($token)->assertOk();

        $this->withHeader('Authorization', 'Bearer '.$token)
            ->patchJson('/api/v1/auth/me', [
                'username' => 'NewName',
                'currentPassword' => 'not my password',
            ])
            ->assertStatus(403)
            ->assertJsonPath('code', 'INVALID_PASSWORD');

        $this->assertSame('AshKetchum', User::query()->firstOrFail()->username);
    }

    public function test_update_changes_the_profile_and_the_password(): void
    {
        $this->useFakeVerifier();

        $token = $this->signIn();
        $this->register($token)->assertOk();

        $this->withHeader('Authorization', 'Bearer '.$token)
            ->patchJson('/api/v1/auth/me', [
                'username' => 'AshMaster',
                'mlbbId' => '987654321',
                'currentPassword' => 'correct horse battery',
                'newPassword' => 'a brand new passphrase',
            ])
            ->assertOk()
            ->assertJsonPath('data.username', 'AshMaster')
            ->assertJsonPath('data.mlbbId', '987654321');

        $user = User::query()->firstOrFail();
        $this->assertTrue(Passwords::verify('a brand new passphrase', $user->password_hash));
        $this->assertFalse(Passwords::verify('correct horse battery', $user->password_hash));
    }

    // -- Security primitives -------------------------------------------------

    public function test_session_tokens_are_not_stored_raw(): void
    {
        $this->useFakeVerifier();

        $token = $this->signIn();

        $session = UserSession::query()->firstOrFail();
        $this->assertSame(hash('sha256', $token), $session->token_hash);
        $this->assertNotSame($token, $session->token_hash);
    }
}
