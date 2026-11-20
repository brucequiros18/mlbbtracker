<?php

namespace App\Http\Controllers\Api;

use App\Exceptions\ApiException;
use App\Http\Controllers\Controller;
use App\Services\EsportsService;
use App\Support\ApiEnvelope;
use Illuminate\Http\JsonResponse;

/**
 * Esports endpoints: professional league standings (MPL ID/PH/MY/KH).
 */
class EsportsController extends Controller
{
    public function standings(string $league, EsportsService $esports): JsonResponse
    {
        if (! in_array($league, EsportsService::LEAGUES, true)) {
            throw ApiException::validation(
                'The league must be one of: '.implode(', ', EsportsService::LEAGUES).'.'
            );
        }

        $data = $esports->standings($league);

        return response()->json(ApiEnvelope::list($data, [
            'sources' => [ApiEnvelope::roneSource()],
        ]));
    }
}
