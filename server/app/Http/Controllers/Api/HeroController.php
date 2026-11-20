<?php

namespace App\Http\Controllers\Api;

use App\Exceptions\ApiException;
use App\Http\Controllers\Controller;
use App\Services\HeroService;
use App\Support\ApiEnvelope;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

/**
 * Hero endpoints. All data is real, sourced from the enabled providers.
 */
class HeroController extends Controller
{
    /**
     * @var list<string>
     */
    private const RANK_WINDOWS = ['1', '3', '7', '15', '30'];

    /**
     * @var list<string>
     */
    private const RANK_TIERS = ['all', 'epic', 'legend', 'mythic', 'honor', 'glory'];

    /**
     * @var list<string>
     */
    private const SORT_FIELDS = ['win_rate', 'ban_rate', 'pick_rate'];

    public function index(Request $request, HeroService $heroes): JsonResponse
    {
        $data = $heroes->catalog(
            $request->query('role') !== null ? (string) $request->query('role') : null,
            $request->query('lane') !== null ? (string) $request->query('lane') : null,
        );

        return response()->json(ApiEnvelope::list($data, [
            'sources' => [ApiEnvelope::roneSource(), ApiEnvelope::dexSource()],
        ]));
    }

    public function rankings(Request $request, HeroService $heroes): JsonResponse
    {
        $days = (string) ($request->query('days') ?? '7');
        $rank = (string) ($request->query('rank') ?? 'all');
        $sort = (string) ($request->query('sort') ?? 'win_rate');

        if (! in_array($days, self::RANK_WINDOWS, true)) {
            throw ApiException::validation('The window must be one of: '.implode(', ', self::RANK_WINDOWS).'.');
        }

        if (! in_array($rank, self::RANK_TIERS, true)) {
            throw ApiException::validation('The rank tier must be one of: '.implode(', ', self::RANK_TIERS).'.');
        }

        if (! in_array($sort, self::SORT_FIELDS, true)) {
            throw ApiException::validation('The sort field must be one of: '.implode(', ', self::SORT_FIELDS).'.');
        }

        $data = $heroes->rankings((int) $days, $rank, $sort);

        return response()->json(ApiEnvelope::list($data, [
            'sources' => [ApiEnvelope::roneSource(), ApiEnvelope::dexSource()],
        ]));
    }

    public function trends(Request $request, string $identifier, HeroService $heroes): JsonResponse
    {
        $days = (string) ($request->query('days') ?? '7');

        if (! in_array($days, self::RANK_WINDOWS, true)) {
            throw ApiException::validation('The window must be one of: '.implode(', ', self::RANK_WINDOWS).'.');
        }

        $data = $heroes->trends($identifier, (int) $days);

        return response()->json(ApiEnvelope::list($data, [
            'sources' => [ApiEnvelope::roneSource()],
        ]));
    }

    public function history(string $identifier, HeroService $heroes): JsonResponse
    {
        $data = $heroes->history($identifier);
        $note = $data === []
            ? 'No snapshots recorded yet. They accumulate as the server fetches rankings live (one per UTC day).'
            : null;

        return response()->json(ApiEnvelope::list($data, ['note' => $note]));
    }

    public function show(string $identifier, HeroService $heroes): JsonResponse
    {
        return response()->json(ApiEnvelope::item($heroes->hero($identifier), [
            'sources' => [ApiEnvelope::roneSource(), ApiEnvelope::dexSource()],
        ]));
    }
}
