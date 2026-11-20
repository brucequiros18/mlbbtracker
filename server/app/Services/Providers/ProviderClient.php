<?php

namespace App\Services\Providers;

use App\Exceptions\ApiException;
use App\Services\ProviderHealthRecorder;
use Illuminate\Http\Client\ConnectionException;
use Illuminate\Http\Client\Response;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;

/**
 * Shared HTTP client for provider adapters.
 *
 * Translates transport and HTTP failures into the typed API errors and
 * records every call in the provider health log.
 */
class ProviderClient
{
    public function __construct(private readonly ProviderHealthRecorder $health) {}

    /**
     * @param  array<string, mixed>  $query
     * @return array<string, mixed>
     */
    public function getJson(string $provider, string $url, array $query = [], ?string $bearer = null): array
    {
        return $this->request($provider, 'GET', $url, $query, null, $bearer);
    }

    /**
     * @param  array<string, mixed>  $payload
     * @return array<string, mixed>
     */
    public function postJson(string $provider, string $url, array $payload = [], ?string $bearer = null): array
    {
        return $this->request($provider, 'POST', $url, [], $payload, $bearer);
    }

    /**
     * @param  array<string, mixed>  $query
     * @param  array<string, mixed>|null  $payload
     * @return array<string, mixed>
     */
    private function request(
        string $provider,
        string $method,
        string $url,
        array $query,
        ?array $payload,
        ?string $bearer,
    ): array {
        $endpoint = (string) parse_url($url, PHP_URL_PATH);
        $startedAt = microtime(true);

        try {
            $request = Http::withHeaders([
                'user-agent' => (string) config('mlbb.http_user_agent'),
                'accept' => 'application/json',
            ])
                ->timeout((float) config('mlbb.http_timeout'));

            if ($bearer !== null) {
                $request = $request->withToken($bearer);
            }

            $response = $method === 'GET'
                ? $request->get($url, $query)
                : $request->post($url, $payload ?? []);
        } catch (ConnectionException $exception) {
            $latency = (int) round((microtime(true) - $startedAt) * 1000);
            $this->health->record($provider, $endpoint, 'error', null, $latency, 'transport');
            Log::warning("provider transport error url={$url} err={$exception->getMessage()}");

            throw ApiException::providerUnavailable('The upstream provider is unreachable.');
        }

        $latency = (int) round((microtime(true) - $startedAt) * 1000);
        $statusCode = $response->status();

        if ($statusCode >= 400) {
            $this->health->record($provider, $endpoint, 'error', $statusCode, $latency, "http_{$statusCode}");
        } else {
            $this->health->record($provider, $endpoint, 'ok', $statusCode, $latency);
        }

        if ($statusCode === 401) {
            throw ApiException::providerAuth(
                'The provider rejected the session token. It has expired or been revoked.'
            );
        }

        if ($statusCode >= 500) {
            throw ApiException::providerUnavailable("Provider returned {$statusCode}.");
        }

        if ($statusCode >= 400) {
            throw ApiException::providerError("Provider rejected the request ({$statusCode}).");
        }

        $decoded = $response->json();

        if (! is_array($decoded)) {
            throw ApiException::providerError('Provider returned a non-JSON response.');
        }

        return $decoded;
    }

    /**
     * Whether a response body carries the provider's `code: 0` success flag.
     *
     * @param  array<string, mixed>  $payload
     */
    public function isSuccess(array $payload): bool
    {
        return ($payload['code'] ?? null) === 0;
    }

    /**
     * The provider's `data` object, when present.
     *
     * @param  array<string, mixed>  $payload
     * @return array<string, mixed>|null
     */
    public function data(array $payload): ?array
    {
        $data = $payload['data'] ?? null;

        return is_array($data) ? $data : null;
    }

    /**
     * The provider's human-readable message, when present.
     *
     * @param  array<string, mixed>  $payload
     */
    public function message(array $payload, string $fallback): string
    {
        foreach (['message', 'msg'] as $key) {
            $value = $payload[$key] ?? null;
            if (is_string($value) && trim($value) !== '') {
                return $value;
            }
        }

        return $fallback;
    }

    /**
     * Whether the response looks like a well-formed provider payload.
     */
    public function looksValid(Response $response): bool
    {
        return $response->successful() && is_array($response->json());
    }
}
