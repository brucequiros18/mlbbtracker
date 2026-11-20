<?php

namespace App\Services;

use App\Exceptions\ApiException;
use App\Models\User;
use App\Models\UserSession;
use App\Support\Passwords;
use Illuminate\Support\Facades\Log;

/**
 * App accounts: Google or Firebase sign-in, profile setup and sessions.
 *
 * Sign-in credentials are **verified ID tokens only** (Google or Firebase) -
 * everything else is app-only profile data:
 *
 * - `username` - chosen by the player, unique (case-insensitive);
 * - `mlbb_id` - self-declared and never verified against Moonton;
 * - `password` - stored as an Argon2id hash, never sent to Moonton, never
 *   used to sign in; it only confirms changes to the profile.
 *
 * Sessions are opaque bearer tokens; only their SHA-256 digest is stored.
 */
class AuthService
{
    private const GOOGLE_NOT_CONFIGURED = 'Google sign-in is not configured on this server yet. Set MLBB_GOOGLE_CLIENT_ID to the OAuth 2.0 web client ID.';

    private const FIREBASE_NOT_CONFIGURED = 'Firebase sign-in is not configured on this server yet. Set MLBB_FIREBASE_PROJECT_ID to the Firebase project ID.';

    private const SESSION_EXPIRED = 'Your session has expired. Please sign in again.';

    public const USERNAME_PATTERN = '/^[A-Za-z0-9_]{3,24}$/';

    public const MLBB_ID_PATTERN = '/^\d{4,20}$/';

    public function __construct(
        private readonly ?GoogleTokenVerifier $verifier,
        private readonly ?FirebaseTokenVerifier $firebaseVerifier = null,
    ) {}

    public function googleEnabled(): bool
    {
        return $this->verifier !== null;
    }

    public function firebaseEnabled(): bool
    {
        return $this->firebaseVerifier !== null;
    }

    /**
     * Verify a Google ID token, then create an app session for it.
     *
     * @return array{sessionToken: string, user: array<string, mixed>, isNewUser: bool}
     */
    public function signInWithGoogle(string $credential): array
    {
        if ($this->verifier === null) {
            throw ApiException::googleNotConfigured(self::GOOGLE_NOT_CONFIGURED);
        }

        $identity = $this->verifier->verify($credential);
        $user = User::query()->where('google_sub', $identity['subject'])->first();
        $isNewUser = $user === null;

        if ($user === null) {
            $user = User::query()->create([
                'google_sub' => $identity['subject'],
                'email' => $identity['email'],
                'email_verified' => $identity['email_verified'],
                'google_name' => $identity['name'],
                'picture_url' => $identity['picture'],
                'last_login_at' => now(),
            ]);
        } else {
            $user->forceFill([
                'email' => $identity['email'],
                'email_verified' => $identity['email_verified'],
                'google_name' => $identity['name'] ?? $user->google_name,
                'picture_url' => $identity['picture'] ?? $user->picture_url,
                'last_login_at' => now(),
            ])->save();
        }

        return $this->startSession($user, $isNewUser, 'google');
    }

    /**
     * Verify a Firebase ID token (email + password sign-in), then create an
     * app session for it. The Firebase UID (`sub`) is the account key.
     *
     * @return array{sessionToken: string, user: array<string, mixed>, isNewUser: bool}
     */
    public function signInWithFirebase(string $idToken): array
    {
        if ($this->firebaseVerifier === null) {
            throw ApiException::googleNotConfigured(self::FIREBASE_NOT_CONFIGURED);
        }

        $identity = $this->firebaseVerifier->verify($idToken);
        $user = User::query()->where('firebase_uid', $identity['subject'])->first();
        $isNewUser = $user === null;

        if ($user === null) {
            $user = User::query()->create([
                'firebase_uid' => $identity['subject'],
                'email' => $identity['email'],
                'email_verified' => $identity['email_verified'],
                'last_login_at' => now(),
            ]);
        } else {
            $user->forceFill([
                'email' => $identity['email'],
                'email_verified' => $identity['email_verified'],
                'last_login_at' => now(),
            ])->save();
        }

        return $this->startSession($user, $isNewUser, 'firebase');
    }

    /**
     * Issue a new opaque session token for the account.
     *
     * @return array{sessionToken: string, user: array<string, mixed>, isNewUser: bool}
     */
    private function startSession(User $user, bool $isNewUser, string $method): array
    {
        $token = $this->generateSessionToken();

        UserSession::query()->create([
            'token_hash' => hash('sha256', $token),
            'user_id' => $user->id,
            'expires_at' => now()->addDays((int) config('mlbb.user_session_ttl_days')),
            'last_seen_at' => now(),
        ]);

        Log::info("{$method} sign-in: user={$user->id} new={$isNewUser}");

        return [
            'sessionToken' => $token,
            'user' => $this->mapUser($user),
            'isNewUser' => $isNewUser,
        ];
    }

    /**
     * Complete the profile of a freshly signed-in account.
     *
     * @return array<string, mixed>
     */
    public function register(string $token, string $username, string $mlbbId, string $password): array
    {
        $user = $this->requireUser($token);

        if ($user->username !== null) {
            throw ApiException::profileAlreadyComplete(
                'This account already has a profile. Change it with PATCH /api/v1/auth/me.'
            );
        }

        $this->ensureUsernameFree($username, $user->id);

        $user->forceFill([
            'username' => $username,
            'mlbb_id' => $mlbbId,
            'password_hash' => Passwords::hash($password),
        ])->save();

        return $this->mapUser($user);
    }

    /**
     * Resolve a bearer token to its account, or fail with 401.
     */
    public function requireUser(string $token): User
    {
        if ($token === '') {
            throw ApiException::authRequired('Sign in with Google to continue.');
        }

        $session = UserSession::query()
            ->where('token_hash', hash('sha256', $token))
            ->first();

        if ($session === null) {
            throw ApiException::authRequired(self::SESSION_EXPIRED);
        }

        if ($session->expires_at->isPast()) {
            $session->delete();

            throw ApiException::authRequired(self::SESSION_EXPIRED);
        }

        $user = $session->user;

        if ($user === null) {
            $session->delete();

            throw ApiException::authRequired(self::SESSION_EXPIRED);
        }

        $this->touchSession($session);

        return $user;
    }

    /**
     * Change profile fields, confirmed with the app password.
     *
     * @return array<string, mixed>
     */
    public function updateProfile(
        string $token,
        ?string $username,
        ?string $mlbbId,
        string $currentPassword,
        ?string $newPassword,
    ): array {
        $user = $this->requireUser($token);

        if (! Passwords::verify($currentPassword, $user->password_hash)) {
            throw ApiException::invalidPassword(
                'That app password did not match, so nothing was changed.'
            );
        }

        if ($username !== null && $username !== $user->username) {
            $this->ensureUsernameFree($username, $user->id);
        }

        if ($username !== null) {
            $user->username = $username;
        }

        if ($mlbbId !== null) {
            $user->mlbb_id = $mlbbId;
        }

        if ($newPassword !== null && $newPassword !== '') {
            $user->password_hash = Passwords::hash($newPassword);
        }

        $user->save();

        return $this->mapUser($user);
    }

    /**
     * Forget the session on the server.
     */
    public function signOut(string $token): void
    {
        if ($token === '') {
            return;
        }

        UserSession::query()
            ->where('token_hash', hash('sha256', $token))
            ->delete();
    }

    /**
     * @return array<string, mixed>
     */
    public function mapUser(User $user): array
    {
        return [
            'id' => $user->id,
            'email' => $user->email,
            'googleName' => $user->google_name,
            'pictureUrl' => $user->picture_url,
            'username' => $user->username,
            'mlbbId' => $user->mlbb_id,
            'profileComplete' => $user->hasCompleteProfile(),
            // The MLBB ID is typed in by the player; it is never verified.
            'mlbbIdVerified' => false,
            'createdAt' => $user->created_at?->utc()->format('Y-m-d\TH:i:s.u\Z'),
            'lastLoginAt' => $user->last_login_at?->utc()->format('Y-m-d\TH:i:s.u\Z'),
        ];
    }

    private function touchSession(UserSession $session): void
    {
        $now = now();

        if ($session->last_seen_at !== null && $now->diffInSeconds($session->last_seen_at) < 3600) {
            return;
        }

        $session->forceFill([
            'last_seen_at' => $now,
            'expires_at' => $now->addDays((int) config('mlbb.user_session_ttl_days')),
        ])->save();
    }

    private function ensureUsernameFree(string $username, int $userId): void
    {
        $existing = User::query()
            ->whereRaw('lower(username) = ?', [mb_strtolower($username)])
            ->first();

        if ($existing !== null && $existing->id !== $userId) {
            throw ApiException::usernameTaken("@{$username} is already taken.");
        }
    }

    private function generateSessionToken(): string
    {
        return rtrim(strtr(base64_encode(random_bytes(32)), '+/', '-_'), '=');
    }
}
