<?php

namespace App\Http\Controllers\Api;

use App\Exceptions\ApiException;
use App\Http\Controllers\Controller;
use App\Models\ProviderHealthEvent;
use App\Services\ProviderHealthRecorder;
use App\Services\Providers\MlbbdexProvider;
use App\Services\Providers\RoneArenaProvider;
use Illuminate\Cache\DatabaseStore;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;

/**
 * Health endpoints.
 */
class HealthController extends Controller
{
    public function health(): JsonResponse
    {
        return response()->json([
            'status' => 'ok',
            'app' => config('mlbb.app_name'),
            'environment' => app()->environment(),
            'cache' => [
                'store' => config('cache.default'),
                'entries' => Cache::getStore() instanceof DatabaseStore
                    ? \DB::table(config('cache.stores.database.table', 'cache'))->count()
                    : null,
            ],
            'providers' => [
                'hero_identity' => config('mlbb.enable_rone') ? RoneArenaProvider::NAME : null,
                'hero_meta' => config('mlbb.enable_mlbbdex') ? MlbbdexProvider::NAME : null,
                'ranking' => config('mlbb.enable_rone')
                    ? RoneArenaProvider::NAME
                    : (config('mlbb.enable_mlbbdex') ? MlbbdexProvider::NAME : null),
                'player' => config('mlbb.enable_rone') ? RoneArenaProvider::NAME : 'none',
            ],
            'capabilities' => [
                'hero_catalog' => (bool) config('mlbb.enable_rone'),
                'hero_detail' => (bool) config('mlbb.enable_mlbbdex'),
                'hero_rankings' => (bool) (config('mlbb.enable_rone') || config('mlbb.enable_mlbbdex')),
                // Anonymous lookup of another player is not supported by any
                // permitted source; the consented self-connect flow is.
                'player_lookup' => (bool) config('mlbb.enable_player_lookup'),
                'player_connection' => (bool) config('mlbb.enable_rone'),
                'web_app' => is_dir(public_path('app')),
                'google_sign_in' => (string) config('mlbb.google_client_id') !== '',
            ],
        ]);
    }

    /**
     * Issue a lightweight live call to each provider and report reachability.
     */
    public function providers(RoneArenaProvider $rone, MlbbdexProvider $dex): JsonResponse
    {
        $results = [];

        if (config('mlbb.enable_rone')) {
            try {
                $results[RoneArenaProvider::NAME] = ['status' => 'up', 'heroes' => count($rone->fetchHeroRefs())];
            } catch (ApiException $exception) {
                $results[RoneArenaProvider::NAME] = ['status' => 'down', 'error' => $exception->payload()['code']];
            }
        }

        if (config('mlbb.enable_mlbbdex')) {
            try {
                $results[MlbbdexProvider::NAME] = ['status' => 'up', 'heroes' => count($dex->fetchHeroCatalog())];
            } catch (ApiException $exception) {
                $results[MlbbdexProvider::NAME] = ['status' => 'down', 'error' => $exception->payload()['code']];
            }
        }

        return response()->json(['status' => 'ok', 'providers' => $results]);
    }

    /**
     * The provider health log - what actually happened, as recorded.
     */
    public function history(Request $request, ProviderHealthRecorder $recorder): JsonResponse
    {
        $limit = (int) ($request->query('limit') ?? 50);

        if ($limit < 1 || $limit > 200) {
            throw ApiException::validation('The limit must be between 1 and 200.');
        }

        $events = $recorder->recent($limit);

        return response()->json([
            'status' => 'ok',
            'count' => count($events),
            'events' => array_map(fn (ProviderHealthEvent $event) => [
                'provider' => $event->provider,
                'endpoint' => $event->endpoint,
                'status' => $event->status,
                'statusCode' => $event->status_code,
                'latencyMs' => $event->latency_ms,
                'errorCode' => $event->error_code,
                'checkedAt' => $event->checked_at?->utc()->format('Y-m-d\TH:i:s.u\Z'),
            ], $events),
        ]);
    }
}
