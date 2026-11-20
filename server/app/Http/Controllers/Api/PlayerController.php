<?php

namespace App\Http\Controllers\Api;

use App\Exceptions\ApiException;
use App\Http\Controllers\Controller;
use App\Http\Requests\Api\ConnectRequest;
use App\Http\Requests\Api\ConnectVerifyRequest;
use App\Services\PlayerService;
use App\Support\ApiEnvelope;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

/**
 * Player endpoints.
 *
 * The app connects **the player's own account**. No password is ever
 * requested: the player receives a one-time code in their in-game mailbox and
 * exchanges it for a session. The upstream JWT stays on the backend; the app
 * only receives an opaque session key, sent back as
 * `Authorization: Bearer <sessionToken>`.
 */
class PlayerController extends Controller
{
    public function connectStart(ConnectRequest $request, PlayerService $players): JsonResponse
    {
        $players->startConnect(
            (string) $request->validated('playerId'),
            (string) $request->validated('zoneId'),
        );

        return response()->json(ApiEnvelope::item([
            'sent' => true,
            'message' => 'A verification code was sent to your in-game mailbox. It expires in a few minutes.',
        ]));
    }

    public function connectVerify(ConnectVerifyRequest $request, PlayerService $players): JsonResponse
    {
        $result = $players->verifyConnect(
            (string) $request->validated('playerId'),
            (string) $request->validated('zoneId'),
            (string) $request->validated('code'),
        );

        return response()->json(ApiEnvelope::item($result));
    }

    public function disconnect(Request $request, PlayerService $players): JsonResponse
    {
        $players->disconnect($this->sessionToken($request));

        return response()->json(ApiEnvelope::item(['disconnected' => true]));
    }

    public function profile(Request $request, PlayerService $players): JsonResponse
    {
        return response()->json(ApiEnvelope::item($players->profile($this->sessionToken($request))));
    }

    public function stats(Request $request, PlayerService $players): JsonResponse
    {
        return response()->json(ApiEnvelope::item($players->stats($this->sessionToken($request))));
    }

    public function matches(Request $request, PlayerService $players): JsonResponse
    {
        $limit = (int) ($request->query('limit') ?? 20);

        if ($limit < 1 || $limit > 50) {
            throw ApiException::validation('The limit must be between 1 and 50.');
        }

        $cursor = $request->query('cursor');
        $page = $players->matches(
            $this->sessionToken($request),
            $limit,
            is_string($cursor) && $cursor !== '' ? $cursor : null,
        );

        return response()->json(ApiEnvelope::item($page, ['count' => count($page['data'])]));
    }

    public function heroes(Request $request, PlayerService $players): JsonResponse
    {
        $limit = (int) ($request->query('limit') ?? 10);

        if ($limit < 1 || $limit > 50) {
            throw ApiException::validation('The limit must be between 1 and 50.');
        }

        $data = $players->frequentHeroes($this->sessionToken($request), $limit);

        return response()->json(ApiEnvelope::list($data));
    }

    /**
     * Anonymous lookup is not supported by any permitted source.
     */
    public function lookup(string $playerId, string $zoneId, PlayerService $players): JsonResponse
    {
        $players->lookup($playerId, $zoneId);

        // The service always throws; this is unreachable.
        return response()->json(ApiEnvelope::item([]), 501);
    }

    private function sessionToken(Request $request): string
    {
        $token = $request->bearerToken();

        if ($token === null || $token === '') {
            throw ApiException::providerAuth(
                'Connect your MLBB account first: POST /players/connect/start, then /connect/verify.'
            );
        }

        return $token;
    }
}
