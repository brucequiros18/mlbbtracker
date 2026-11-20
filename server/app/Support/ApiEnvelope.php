<?php

namespace App\Support;

/**
 * The shared response envelope.
 *
 * Every endpoint answers with `{"data": ..., "meta": ...}` so clients have one
 * shape to parse. `meta` carries attribution and freshness information - the
 * upstream licenses (CC BY-SA wiki data) require crediting the source.
 */
final class ApiEnvelope
{
    /**
     * @param  list<mixed>  $data
     * @param  array<string, mixed>  $meta
     * @return array{data: list<mixed>, meta: array<string, mixed>}
     */
    public static function list(array $data, array $meta = []): array
    {
        return [
            'data' => $data,
            'meta' => self::meta($meta + ['count' => count($data)]),
        ];
    }

    /**
     * @param  array<string, mixed>  $meta
     * @return array{data: mixed, meta: array<string, mixed>}
     */
    public static function item(mixed $data, array $meta = []): array
    {
        return [
            'data' => $data,
            'meta' => self::meta($meta),
        ];
    }

    /**
     * @param  array<string, mixed>  $meta
     * @return array<string, mixed>
     */
    public static function meta(array $meta = []): array
    {
        return array_merge([
            'generatedAt' => now()->utc()->format('Y-m-d\TH:i:s.u\Z'),
            'cached' => false,
            'count' => null,
            'note' => null,
            'sources' => [],
        ], $meta);
    }

    /**
     * @return array{name: string, url: string, license: string}
     */
    public static function roneSource(): array
    {
        return [
            'name' => 'Rone Arena API',
            'url' => 'https://arena.rone.dev/',
            'license' => 'Unofficial community API; game data from Moonton public services',
        ];
    }

    /**
     * @return array{name: string, url: string, license: string}
     */
    public static function dexSource(): array
    {
        return [
            'name' => 'MLBBDex',
            'url' => 'https://mlbbdex.com/',
            'license' => 'CC BY-SA (Mobile Legends wiki) + MIT (written analysis)',
        ];
    }
}
