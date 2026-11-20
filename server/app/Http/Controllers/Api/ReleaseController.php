<?php

namespace App\Http\Controllers\Api;

use App\Exceptions\ApiException;
use App\Http\Controllers\Controller;
use App\Services\ReleaseService;
use App\Support\ApiEnvelope;
use Illuminate\Http\JsonResponse;

/**
 * The published app-release manifest (used by the download page and clients).
 */
class ReleaseController extends Controller
{
    public function show(ReleaseService $releases): JsonResponse
    {
        $manifest = $releases->readManifest();

        if ($manifest === null) {
            throw ApiException::notFound('No app release has been published yet.');
        }

        return response()->json(ApiEnvelope::item($manifest));
    }
}
