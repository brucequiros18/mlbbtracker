<?php

namespace App\Services\Providers;

use App\Exceptions\ApiException;

/**
 * MLBBDex adapter (`https://mlbbdex.com/api/v1`).
 *
 * No key, no quota, static cached JSON. Source data is the Mobile Legends wiki
 * under CC BY-SA, with ranked stats re-served from the arena.rone.dev
 * community API. The response envelope carries the attribution, which we
 * preserve.
 *
 * Verified endpoints (see docs/API_DOCUMENTATION.md):
 *
 * - `GET /heroes` - slug, name, roles, lanes, specialties.
 * - `GET /heroes/{slug}` - full profile: stats, skills with descriptions.
 * - `GET /rankings` - tier plus win/ban/pick rates.
 * - `GET /patches` - patch list.
 */
class MlbbdexProvider
{
    public const NAME = 'mlbbdex';

    private string $base;

    public function __construct(private readonly ProviderClient $client)
    {
        $this->base = rtrim((string) config('mlbb.mlbbdex_base_url'), '/');
    }

    /**
     * @return list<array{slug: string, name: string, roles: list<string>, lanes: list<string>, specialties: list<string>}>
     */
    public function fetchHeroCatalog(): array
    {
        $payload = $this->client->getJson(self::NAME, $this->base.'/heroes');
        $rows = $this->rows($payload);
        $metas = [];

        foreach ($rows as $row) {
            if (! is_string($row['slug'] ?? null) || ! is_string($row['name'] ?? null)) {
                continue;
            }

            $metas[] = [
                'slug' => $row['slug'],
                'name' => $row['name'],
                'roles' => $this->stringList($row['roles'] ?? []),
                'lanes' => $this->stringList($row['lanes'] ?? []),
                'specialties' => $this->stringList($row['specialties'] ?? []),
            ];
        }

        return $metas;
    }

    /**
     * @return array{slug: string, name: string, roles: list<string>, lanes: list<string>, specialties: list<string>, skills: list<array{name: string, description: string}>, stats: array<string, string>}
     */
    public function fetchHeroDetail(string $slug): array
    {
        $payload = $this->client->getJson(self::NAME, $this->base."/heroes/{$slug}");
        $data = is_array($payload['data'] ?? null) ? $payload['data'] : null;

        if ($data === null) {
            throw ApiException::notFound("Hero '{$slug}' was not found.");
        }

        $skills = [];
        $rawSkills = is_array($data['skills'] ?? null) ? $data['skills'] : [];

        foreach ($rawSkills as $skill) {
            if (! is_array($skill)) {
                continue;
            }

            $skills[] = [
                'name' => (string) ($skill['name'] ?? ''),
                'description' => (string) ($skill['description'] ?? ''),
            ];
        }

        $stats = [];
        $rawStats = is_array($data['stats'] ?? null) ? $data['stats'] : [];

        foreach ($rawStats as $key => $value) {
            $stats[(string) $key] = (string) $value;
        }

        return [
            'slug' => (string) ($data['slug'] ?? $slug),
            'name' => (string) ($data['name'] ?? $slug),
            'roles' => $this->stringList($data['roles'] ?? []),
            'lanes' => $this->stringList($data['lanes'] ?? []),
            'specialties' => $this->stringList($data['specialties'] ?? []),
            'skills' => $skills,
            'stats' => $stats,
        ];
    }

    /**
     * @return list<array{id: ?int, name: string, slug: ?string, head_image: ?string, win_rate: float, ban_rate: float, pick_rate: float, tier: ?string}>
     */
    public function fetchRankings(): array
    {
        // MLBBDex rankings are a single snapshot; days/rank filters are ignored.
        $payload = $this->client->getJson(self::NAME, $this->base.'/rankings');
        $data = is_array($payload['data'] ?? null) ? $payload['data'] : [];
        $heroes = is_array($data['heroes'] ?? null) ? $data['heroes'] : [];
        $entries = [];

        foreach ($heroes as $row) {
            if (! is_array($row) || ! is_string($row['slug'] ?? null)) {
                continue;
            }

            $entries[] = [
                'id' => null,
                'name' => (string) ($row['name'] ?? ''),
                'slug' => $row['slug'],
                'head_image' => null,
                'win_rate' => (float) ($row['winRate'] ?? 0),
                'ban_rate' => (float) ($row['banRate'] ?? 0),
                'pick_rate' => (float) ($row['pickRate'] ?? 0),
                'tier' => is_string($row['tier'] ?? null) ? $row['tier'] : null,
            ];
        }

        return $entries;
    }

    /**
     * @return list<array{version: string, title: string, link: string}>
     */
    public function fetchPatches(): array
    {
        $payload = $this->client->getJson(self::NAME, $this->base.'/patches');
        $rows = $this->rows($payload);
        $patches = [];

        foreach ($rows as $row) {
            $patches[] = [
                'version' => (string) ($row['version'] ?? ''),
                'title' => (string) ($row['title'] ?? ''),
                'link' => (string) ($row['link'] ?? ''),
            ];
        }

        return $patches;
    }

    /**
     * @param  array<string, mixed>  $payload
     * @return list<array<string, mixed>>
     */
    private function rows(array $payload): array
    {
        $data = $payload['data'] ?? null;

        if (! is_array($data)) {
            throw ApiException::providerError("MLBBDex payload had no 'data' list.");
        }

        return array_values(array_filter($data, 'is_array'));
    }

    /**
     * @return list<string>
     */
    private function stringList(mixed $value): array
    {
        if (! is_array($value)) {
            return [];
        }

        return array_values(array_map('strval', array_filter($value, 'is_string')));
    }
}
