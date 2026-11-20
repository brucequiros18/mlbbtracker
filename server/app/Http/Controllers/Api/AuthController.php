<?php

namespace App\Http\Controllers\Api;

use App\Exceptions\ApiException;
use App\Http\Controllers\Controller;
use App\Http\Requests\Api\GoogleSignInRequest;
use App\Http\Requests\Api\RegisterRequest;
use App\Http\Requests\Api\UpdateProfileRequest;
use App\Services\AuthService;
use App\Support\ApiEnvelope;
use App\Support\Passwords;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

/**
 * Account endpoints - sign-in with verified ID tokens (Firebase or Google).
 *
 * 1. GET   /auth/config    which sign-in methods are configured? client IDs
 *                          and the public Firebase web config
 * 2. POST  /auth/firebase  {idToken} from the Firebase JS SDK
 *                          (email + password sign-up/sign-in)
 *                          -> app session token + account
 * 3. POST  /auth/google    {credential} from Google Identity Services
 *                          -> app session token + account
 * 4. POST  /auth/register  complete the profile: username, MLBB ID and the
 *                          app password (needs the session token)
 * 5. GET   /auth/me        the signed-in account
 * 6. PATCH /auth/me        change the profile (confirmed by the app password)
 * 7. POST  /auth/logout    forget the session
 *
 * Sign-in tokens are verified server-side; the browser never decides who the
 * player is. The MLBB ID is **self-declared**: it is stored as typed, never
 * checked against Moonton, and the API says so on every response.
 */
class AuthController extends Controller
{
    private const MLBB_ID_NOTE = 'MLBB ID is self-declared by the player and is not verified.';

    public function config(AuthService $auth): JsonResponse
    {
        $clientId = (string) config('mlbb.google_client_id');
        $googleEnabled = $clientId !== '';
        $projectId = (string) config('mlbb.firebase_project_id');
        $apiKey = (string) config('mlbb.firebase_api_key');
        $firebaseEnabled = $projectId !== '';

        return response()->json(ApiEnvelope::item([
            'googleSignInEnabled' => $googleEnabled,
            'googleClientId' => $googleEnabled ? $clientId : null,
            'firebaseEnabled' => $firebaseEnabled,
            // The web API key and auth domain are public values: they ship in
            // every Firebase web app config and are required by the JS SDK.
            'firebaseApiKey' => $firebaseEnabled && $apiKey !== '' ? $apiKey : null,
            'firebaseAuthDomain' => $firebaseEnabled
                ? ((string) config('mlbb.firebase_auth_domain') !== ''
                    ? (string) config('mlbb.firebase_auth_domain')
                    : $projectId.'.firebaseapp.com')
                : null,
            'firebaseProjectId' => $firebaseEnabled ? $projectId : null,
            'minPasswordLength' => Passwords::MIN_LENGTH,
            'maxPasswordLength' => Passwords::MAX_LENGTH,
            'usernamePattern' => '^[A-Za-z0-9_][A-Za-z0-9_. ]{1,22}[A-Za-z0-9_.]$',
            'mlbbIdPattern' => '^\d{4,20}$',
        ], [
            'note' => $firebaseEnabled || $googleEnabled
                ? 'Sign-in is a verified ID token: Firebase (email + password) or Google.'
                : 'No sign-in method is configured on this server.',
        ]));
    }

    public function firebase(Request $request, AuthService $auth): JsonResponse
    {
        $validated = $request->validate([
            'idToken' => ['required', 'string', 'min:20', 'max:8192'],
        ]);

        $result = $auth->signInWithFirebase((string) $validated['idToken']);

        return response()->json(ApiEnvelope::item($result));
    }

    public function google(GoogleSignInRequest $request, AuthService $auth): JsonResponse
    {
        $result = $auth->signInWithGoogle((string) $request->validated('credential'));

        return response()->json(ApiEnvelope::item($result));
    }

    public function register(RegisterRequest $request, AuthService $auth): JsonResponse
    {
        $data = $auth->register(
            $this->accountToken($request),
            (string) $request->validated('username'),
            (string) $request->validated('mlbbId'),
            (string) $request->validated('password'),
        );

        return response()->json(ApiEnvelope::item($data, ['note' => self::MLBB_ID_NOTE]));
    }

    public function me(Request $request, AuthService $auth): JsonResponse
    {
        $user = $auth->requireUser($this->accountToken($request));

        return response()->json(ApiEnvelope::item($auth->mapUser($user), [
            'note' => self::MLBB_ID_NOTE,
        ]));
    }

    public function updateMe(UpdateProfileRequest $request, AuthService $auth): JsonResponse
    {
        $validated = $request->validated();

        $data = $auth->updateProfile(
            $this->accountToken($request),
            isset($validated['username']) ? $validated['username'] : null,
            isset($validated['mlbbId']) ? $validated['mlbbId'] : null,
            (string) $validated['currentPassword'],
            isset($validated['newPassword']) ? $validated['newPassword'] : null,
        );

        return response()->json(ApiEnvelope::item($data, ['note' => self::MLBB_ID_NOTE]));
    }

    public function logout(Request $request, AuthService $auth): JsonResponse
    {
        $auth->signOut($this->accountToken($request));

        return response()->json(ApiEnvelope::item(['signedOut' => true]));
    }

    private function accountToken(Request $request): string
    {
        $token = $request->bearerToken();

        if ($token === null || $token === '') {
            throw ApiException::authRequired('Sign in with Google to continue.');
        }

        return $token;
    }
}
