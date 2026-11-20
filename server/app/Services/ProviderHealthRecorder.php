<?php

namespace App\Services;

use App\Models\ProviderHealthEvent;
use Illuminate\Support\Facades\Log;

/**
 * Appends one provider call outcome to the health log.
 *
 * The log is what actually happened, as recorded - it is the evidence behind
 * the `/health/history` endpoint.
 */
class ProviderHealthRecorder
{
    public function record(
        string $provider,
        string $endpoint,
        string $status,
        ?int $statusCode = null,
        ?int $latencyMs = null,
        ?string $errorCode = null,
    ): void {
        try {
            ProviderHealthEvent::create([
                'provider' => $provider,
                'endpoint' => $endpoint,
                'status' => $status,
                'status_code' => $statusCode,
                'latency_ms' => $latencyMs,
                'error_code' => $errorCode,
                'checked_at' => now(),
            ]);
        } catch (\Throwable $exception) {
            // The health log must never take the API down.
            Log::warning('could not record provider health: '.$exception->getMessage());
        }
    }

    /**
     * Most recent health events, newest first.
     *
     * @return list<ProviderHealthEvent>
     */
    public function recent(int $limit = 50): array
    {
        return ProviderHealthEvent::query()
            ->orderByDesc('checked_at')
            ->orderByDesc('id')
            ->limit($limit)
            ->get()
            ->all();
    }
}
