<?php

namespace App\Services;

use App\Exceptions\ApiException;
use App\Models\ApiCacheEntry;
use App\Models\HeroSnapshot;
use App\Services\Providers\MlbbdexProvider;
use App\Services\Providers\RoneArenaProvider;
use App\Support\HeroName;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;

/**
 * Hero service: merges providers into the normalized API shapes.
 *
 * Responsibilities:
 *
 * - combine identity (Rone Arena: ids, portraits, relations) with metadata
 *   (MLBBDex: roles, lanes, skills, tiers);
 * - cache provider results with type-appropriate TTLs;
 * - never invent a field - if a provider does not supply something it is left
 *   empty rather than filled with a placeholder value.
 */
class HeroService
{
    public function __construct(
        private readonly RoneArenaProvider $rone,
        private readonly MlbbdexProvider $dex,
    ) {}

    /**
     * @return list<array{id: int, name: string, slug: string, roles: list<string>, lanes: list<string>, headImage: ?string, tier: ?string}>
     */
    public function catalog(?string $role = null, ?string $lane = null): array
    {
        $heroes = $this->catalogRaw();

        if ($role !== null && strtolower($role) !== 'all') {
            $heroes = array_values(array_filter(
                $heroes,
                fn (array $hero) => in_array(strtolower($role), array_map('strtolower', $hero['roles']), true)
            ));
        }

        if ($lane !== null && strtolower($lane) !== 'all') {
            $heroes = array_values(array_filter(
                $heroes,
                fn (array $hero) => in_array(strtolower($lane), array_map('strtolower', $hero['lanes']), true)
            ));
        }

        usort($heroes, fn (array $a, array $b) => strcasecmp($a['name'], $b['name']));

        return $heroes;
    }

    /**
     * @return list<array{id: int, name: string, slug: string, roles: list<string>, lanes: list<string>, headImage: ?string, tier: ?string}>
     */
    public function catalogRaw(): array
    {
        $key = 'catalog:v1';

        $cached = Cache::get($key);
        if (is_array($cached)) {
            return $cached;
        }

        // Cold tier: a restart should not re-fetch the whole catalog upstream.
        $stored = $this->cacheRead($key);
        if ($stored !== null) {
            Cache::put($key, $stored, $this->ttl('cache_ttl_catalog'));

            return $stored;
        }

        $refs = $this->rone->fetchHeroRefs();
        $metas = [];

        try {
            $metas = $this->dex->fetchHeroCatalog();
        } catch (ApiException $exception) {
            Log::warning('hero metadata unavailable: '.$exception->getMessage());
        }

        $metaByKey = [];
        foreach ($metas as $meta) {
            $metaByKey[HeroName::normalize($meta['name'])] = $meta;
        }

        $tiers = $this->tierMap();
        $heroes = [];

        foreach ($refs as $ref) {
            $keyName = HeroName::normalize($ref['name']);
            $meta = $metaByKey[$keyName] ?? null;

            $heroes[] = [
                'id' => $ref['id'],
                'name' => $ref['name'],
                'slug' => $meta['slug'] ?? $keyName,
                'roles' => $meta['roles'] ?? [],
                'lanes' => $meta['lanes'] ?? [],
                'headImage' => $ref['head_image'],
                'tier' => $tiers[$keyName] ?? null,
            ];
        }

        Cache::put($key, $heroes, $this->ttl('cache_ttl_catalog'));
        $this->cacheWrite($key, $heroes);

        return $heroes;
    }

    /**
     * @return array<string, ?string>
     */
    public function tierMap(): array
    {
        $key = 'tiers:v1';

        $cached = Cache::get($key);
        if (is_array($cached)) {
            return $cached;
        }

        $tiers = [];

        try {
            foreach ($this->dex->fetchRankings() as $entry) {
                if (! empty($entry['tier'])) {
                    $tiers[HeroName::normalize($entry['name'])] = $entry['tier'];
                }
            }
        } catch (ApiException $exception) {
            Log::warning('tier map unavailable: '.$exception->getMessage());
        }

        Cache::put($key, $tiers, $this->ttl('cache_ttl_catalog'));

        return $tiers;
    }

    /**
     * @return list<array{id: int, name: string, slug: ?string, headImage: ?string, winRate: float, banRate: float, pickRate: float, tier: ?string}>
     */
    public function rankings(int $days = 7, string $rank = 'all', string $sortField = 'win_rate'): array
    {
        $key = "rankings:v1:{$days}:{$rank}:{$sortField}";

        $cached = Cache::get($key);
        if (is_array($cached)) {
            return $cached;
        }

        $stored = $this->cacheRead($key);
        if ($stored !== null) {
            Cache::put($key, $stored, $this->ttl('cache_ttl_rankings'));

            return $stored;
        }

        $entries = $this->rone->fetchRankings($days, $rank, $sortField);
        $catalog = $this->catalogRaw();
        $byName = [];

        foreach ($catalog as $hero) {
            $byName[HeroName::normalize($hero['name'])] = $hero;
        }

        $tiers = $this->tierMap();
        $rows = [];

        foreach ($entries as $entry) {
            $keyName = HeroName::normalize($entry['name']);
            $known = $byName[$keyName] ?? null;

            $rows[] = [
                'id' => $entry['id'] ?? ($known['id'] ?? 0),
                'name' => $entry['name'],
                'slug' => $entry['slug'] ?? ($known['slug'] ?? $keyName),
                'headImage' => $entry['head_image'] ?? ($known['headImage'] ?? null),
                'winRate' => round($entry['win_rate'], 6),
                'banRate' => round($entry['ban_rate'], 6),
                'pickRate' => round($entry['pick_rate'], 6),
                'tier' => $entry['tier'] ?? ($tiers[$keyName] ?? null),
            ];
        }

        $sortKey = match ($sortField) {
            'ban_rate' => 'banRate',
            'pick_rate' => 'pickRate',
            default => 'winRate',
        };

        usort($rows, fn (array $a, array $b) => $b[$sortKey] <=> $a[$sortKey]);

        Cache::put($key, $rows, $this->ttl('cache_ttl_rankings'));
        $this->cacheWrite($key, $rows);

        // Persist a daily snapshot of the raw provider entries (7-day window
        // only - the canonical analytics window). Failures never break the API.
        if ($days === 7) {
            try {
                $this->recordSnapshots($entries);
            } catch (\Throwable $exception) {
                Log::error('snapshots: recording failed: '.$exception->getMessage());
            }
        }

        return $rows;
    }

    /**
     * @return list<array{date: string, winRate: float, banRate: float, pickRate: float}>
     */
    public function trends(string $identifier, int $days = 7): array
    {
        $catalog = $this->catalogRaw();
        $match = $this->resolve($catalog, $identifier);

        if ($match === null) {
            throw ApiException::notFound("No hero matches '{$identifier}'.");
        }

        $key = "trends:v1:{$match['id']}:{$days}";

        $cached = Cache::get($key);
        if (is_array($cached)) {
            return $cached;
        }

        $points = array_map(
            fn (array $point) => [
                'date' => $point['date'],
                'winRate' => $point['win_rate'],
                'banRate' => $point['ban_rate'],
                'pickRate' => $point['pick_rate'],
            ],
            $this->rone->fetchTrends($match['id'], $days)
        );

        Cache::put($key, $points, $this->ttl('cache_ttl_rankings'));

        return $points;
    }

    /**
     * Recorded daily snapshots for a hero (our own observations).
     *
     * @return list<array{capturedOn: string, winRate: float, banRate: float, pickRate: float, tier: ?string, rankPosition: ?int}>
     */
    public function history(string $identifier): array
    {
        $catalog = $this->catalogRaw();
        $match = $this->resolve($catalog, $identifier);

        if ($match === null) {
            throw ApiException::notFound("No hero matches '{$identifier}'.");
        }

        $snapshots = HeroSnapshot::query()
            ->where('hero_id', $match['id'])
            ->where('days', 7)
            ->orderBy('captured_on')
            ->orderBy('id')
            ->get();

        return $snapshots->map(fn (HeroSnapshot $snapshot) => [
            'capturedOn' => $snapshot->captured_on?->toDateString(),
            'winRate' => $snapshot->win_rate,
            'banRate' => $snapshot->ban_rate,
            'pickRate' => $snapshot->pick_rate,
            'tier' => $snapshot->tier,
            'rankPosition' => $snapshot->rank_position,
        ])->all();
    }

    /**
     * @return array{id: ?int, name: string, slug: string, roles: list<string>, lanes: list<string>, specialties: list<string>, headImage: ?string, portrait: ?string, skills: list<array{name: string, description: string}>, strongAgainst: list<string>, weakAgainst: list<string>, rankStat: ?array{winRate: float, banRate: float, pickRate: float}}
     */
    public function hero(string $identifier): array
    {
        $catalog = $this->catalogRaw();
        $match = $this->resolve($catalog, $identifier);

        if ($match === null) {
            throw ApiException::notFound("No hero matches '{$identifier}'.");
        }

        $detail = $this->dex->fetchHeroDetail($match['slug']);
        $refs = $this->identityRefs();
        $byId = [];

        foreach ($refs as $ref) {
            $byId[$ref['id']] = $ref;
        }

        $self = $byId[$match['id']] ?? null;
        $strong = [];
        $weak = [];

        foreach ($self['strong_ids'] ?? [] as $id) {
            if (isset($byId[$id])) {
                $strong[] = $byId[$id]['name'];
            }
        }

        foreach ($self['weak_ids'] ?? [] as $id) {
            if (isset($byId[$id])) {
                $weak[] = $byId[$id]['name'];
            }
        }

        return [
            'id' => $match['id'],
            'name' => $detail['name'],
            'slug' => $detail['slug'],
            'roles' => $detail['roles'],
            'lanes' => $detail['lanes'],
            'specialties' => $detail['specialties'],
            'headImage' => $match['headImage'],
            'portrait' => $match['headImage'],
            'skills' => $detail['skills'],
            'strongAgainst' => $strong,
            'weakAgainst' => $weak,
            'rankStat' => $this->rankStatFor($match['id']),
        ];
    }

    /**
     * @return list<array{id: int, name: string, head_image: ?string, strong_ids: list<int>, weak_ids: list<int>}>
     */
    private function identityRefs(): array
    {
        $key = 'refs:v1';

        $cached = Cache::get($key);
        if (is_array($cached)) {
            return $cached;
        }

        $refs = $this->rone->fetchHeroRefs();
        Cache::put($key, $refs, $this->ttl('cache_ttl_catalog'));

        return $refs;
    }

    /**
     * @return array{winRate: float, banRate: float, pickRate: float}|null
     */
    private function rankStatFor(int $heroId): ?array
    {
        try {
            $rows = $this->rankings(7, 'all', 'win_rate');
        } catch (ApiException) {
            return null;
        }

        foreach ($rows as $row) {
            if ($row['id'] === $heroId) {
                return [
                    'winRate' => $row['winRate'],
                    'banRate' => $row['banRate'],
                    'pickRate' => $row['pickRate'],
                ];
            }
        }

        return null;
    }

    /**
     * @param  list<array{id: ?int, name: string, slug: ?string, head_image: ?string, win_rate: float, ban_rate: float, pick_rate: float, tier: ?string}>  $entries
     */
    private function recordSnapshots(array $entries): int
    {
        $today = now()->utc()->toDateString();
        $existing = HeroSnapshot::query()
            ->where('days', 7)
            ->whereDate('captured_on', $today)
            ->pluck('hero_id')
            ->all();

        $fresh = [];

        foreach ($entries as $entry) {
            $heroId = $entry['id'] ?? null;
            if ($heroId === null || in_array($heroId, $existing, true)) {
                continue;
            }

            $fresh[] = [
                'hero_id' => $heroId,
                'hero_name' => mb_substr($entry['name'], 0, 64),
                'days' => 7,
                'captured_on' => $today,
                'win_rate' => $entry['win_rate'],
                'ban_rate' => $entry['ban_rate'],
                'pick_rate' => $entry['pick_rate'],
                'tier' => $entry['tier'] !== null ? mb_substr($entry['tier'], 0, 16) : null,
                'rank_position' => null,
                'created_at' => now(),
                'updated_at' => now(),
            ];
        }

        if ($fresh === []) {
            return 0;
        }

        HeroSnapshot::insert($fresh);

        return count($fresh);
    }

    /**
     * @param  list<array{id: int, name: string, slug: string, roles: list<string>, lanes: list<string>, headImage: ?string, tier: ?string}>  $catalog
     * @return array{id: int, name: string, slug: string, roles: list<string>, lanes: list<string>, headImage: ?string, tier: ?string}|null
     */
    private function resolve(array $catalog, string $identifier): ?array
    {
        if (ctype_digit($identifier)) {
            foreach ($catalog as $hero) {
                if ($hero['id'] === (int) $identifier) {
                    return $hero;
                }
            }

            return null;
        }

        $key = HeroName::normalize($identifier);

        foreach ($catalog as $hero) {
            if (HeroName::normalize($hero['slug']) === $key || HeroName::normalize($hero['name']) === $key) {
                return $hero;
            }
        }

        return null;
    }

    /**
     * @return list<mixed>|null
     */
    private function cacheRead(string $key): ?array
    {
        try {
            $entry = ApiCacheEntry::query()->where('cache_key', $key)->first();

            if ($entry === null) {
                return null;
            }

            if ($entry->expires_at !== null && $entry->expires_at->isPast()) {
                $entry->delete();

                return null;
            }

            return is_array($entry->payload) ? $entry->payload : null;
        } catch (\Throwable $exception) {
            Log::error("cache read failed for {$key}: ".$exception->getMessage());

            return null;
        }
    }

    /**
     * @param  list<mixed>  $rows
     */
    private function cacheWrite(string $key, array $rows): void
    {
        try {
            ApiCacheEntry::query()->updateOrCreate(
                ['cache_key' => $key],
                [
                    'provider' => 'rone_arena+mlbbdex',
                    'payload' => $rows,
                    'expires_at' => now()->addSeconds($this->ttl(
                        str_starts_with($key, 'rankings') ? 'cache_ttl_rankings' : 'cache_ttl_catalog'
                    )),
                ]
            );
        } catch (\Throwable $exception) {
            Log::error("cache write failed for {$key}: ".$exception->getMessage());
        }
    }

    private function ttl(string $key): int
    {
        return (int) config('mlbb.'.$key);
    }
}
