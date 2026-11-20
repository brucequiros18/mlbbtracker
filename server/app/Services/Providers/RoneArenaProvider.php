<?php

namespace App\Services\Providers;

use App\Exceptions\ApiException;

/**
 * Rone Arena adapter (`https://arena.rone.dev/api`).
 *
 * Unofficial, community-maintained API that re-serves Moonton's public game
 * services. It is the source of canonical hero ids, portraits and hero
 * win/ban/pick rankings. It requires no API key for public endpoints.
 *
 * Verified endpoints (see docs/API_DOCUMENTATION.md):
 *
 * - `GET /heroes?size=&index=` - hero ids, names, portraits, relations.
 * - `GET /heroes/rank?days=&rank=&sort_field=&size=` - hero rankings.
 */
class RoneArenaProvider
{
    public const NAME = 'rone_arena';

    private const PAGE_SIZE = 50;

    private const MAX_PAGES = 8;

    private string $base;

    public function __construct(private readonly ProviderClient $client)
    {
        $this->base = rtrim((string) config('mlbb.rone_base_url'), '/');
    }

    /**
     * @return list<array{id: int, name: string, head_image: ?string, strong_ids: list<int>, weak_ids: list<int>}>
     */
    public function fetchHeroRefs(): array
    {
        $refs = [];
        $total = null;

        for ($index = 1; $index <= self::MAX_PAGES; $index++) {
            $payload = $this->client->getJson(self::NAME, $this->base.'/heroes', [
                'size' => self::PAGE_SIZE,
                'index' => $index,
                'lang' => 'en',
            ]);

            $data = $this->client->data($payload);

            if ($data === null) {
                throw ApiException::providerError("Rone Arena 'heroes' payload was malformed.");
            }

            $records = is_array($data['records'] ?? null) ? $data['records'] : [];

            if ($total === null && is_int($data['total'] ?? null)) {
                $total = $data['total'];
            }

            if ($records === []) {
                break;
            }

            foreach ($records as $record) {
                $ref = $this->parseRef($record);
                if ($ref !== null) {
                    $refs[] = $ref;
                }
            }

            if ($total !== null && count($refs) >= $total) {
                break;
            }
        }

        if ($refs === []) {
            throw ApiException::providerError('Rone Arena returned no heroes.');
        }

        return $refs;
    }

    /**
     * @return list<array{id: ?int, name: string, slug: ?string, head_image: ?string, win_rate: float, ban_rate: float, pick_rate: float, tier: ?string}>
     */
    public function fetchRankings(int $days, string $rank, string $sortField): array
    {
        $payload = $this->client->getJson(self::NAME, $this->base.'/heroes/rank', [
            'days' => $days,
            'rank' => $rank,
            'sort_field' => $sortField,
            'sort_order' => 'desc',
            'size' => 200,
            'lang' => 'en',
        ]);

        $data = $this->client->data($payload);

        if ($data === null) {
            throw ApiException::providerError("Rone Arena 'heroes/rank' payload was malformed.");
        }

        $entries = [];
        $records = is_array($data['records'] ?? null) ? $data['records'] : [];

        foreach ($records as $record) {
            $inner = is_array($record['data'] ?? null) ? $record['data'] : [];
            $hero = is_array($inner['main_hero']['data'] ?? null) ? $inner['main_hero']['data'] : [];
            $heroId = $inner['main_heroid'] ?? null;
            $name = $hero['name'] ?? null;

            if ($heroId === null || ! is_string($name) || $name === '') {
                continue;
            }

            $entries[] = [
                'id' => (int) $heroId,
                'name' => $name,
                'slug' => null,
                'head_image' => is_string($hero['head'] ?? null) ? $hero['head'] : null,
                'win_rate' => (float) ($inner['main_hero_win_rate'] ?? 0),
                'ban_rate' => (float) ($inner['main_hero_ban_rate'] ?? 0),
                'pick_rate' => (float) ($inner['main_hero_appearance_rate'] ?? 0),
                'tier' => null,
            ];
        }

        return $entries;
    }

    /**
     * @return list<array{date: string, win_rate: float, ban_rate: float, pick_rate: float}>
     */
    public function fetchTrends(int $heroId, int $days): array
    {
        $payload = $this->client->getJson(self::NAME, $this->base."/heroes/{$heroId}/trends", [
            'rank' => 'all',
            'past-days' => $days,
            'size' => 1,
            'lang' => 'en',
        ]);

        $data = $this->client->data($payload);

        if ($data === null) {
            throw ApiException::providerError("Rone Arena 'hero trends' payload was malformed.");
        }

        $records = is_array($data['records'] ?? null) ? $data['records'] : [];

        if ($records === []) {
            return [];
        }

        $points = is_array($records[0]['data']['win_rate'] ?? null) ? $records[0]['data']['win_rate'] : [];
        $out = [];

        foreach ($points as $point) {
            if (! is_array($point) || empty($point['date'])) {
                continue;
            }

            $out[] = [
                'date' => (string) $point['date'],
                'win_rate' => (float) ($point['win_rate'] ?? 0),
                'ban_rate' => (float) ($point['ban_rate'] ?? 0),
                'pick_rate' => (float) ($point['app_rate'] ?? 0),
            ];
        }

        // The provider returns newest-first; the API serves oldest-first.
        usort($out, fn (array $a, array $b) => strcmp($a['date'], $b['date']));

        return $out;
    }

    /**
     * @return list<array{rank: int, team_code: string, team_name: string, logo: ?string, match_point: int, match_wins: int, match_losses: int, net_game_win: int, game_wins: int, game_losses: int}>
     */
    public function fetchStandings(string $league): array
    {
        // This endpoint returns a bare {"standings": [...]} object rather than
        // the {"code": 0, "data": {...}} envelope used by the game-data routes.
        $payload = $this->client->getJson(self::NAME, $this->base."/esports/{$league}/standings");
        $rows = is_array($payload['standings'] ?? null) ? $payload['standings'] : null;

        if ($rows === null) {
            throw ApiException::providerError("Rone Arena 'esports standings' payload was malformed.");
        }

        $out = [];

        foreach ($rows as $row) {
            if (! is_array($row)) {
                continue;
            }

            $team = is_array($row['team'] ?? null) ? $row['team'] : [];
            $matchWl = is_array($row['match_wl'] ?? null) ? $row['match_wl'] : [];
            $gameWl = is_array($row['game_wl'] ?? null) ? $row['game_wl'] : [];
            $code = (string) ($team['name'] ?? '');

            $out[] = [
                'rank' => (int) ($row['rank'] ?? 0),
                'team_code' => $code,
                // `full_name` is null for some leagues (e.g. MPL PH).
                'team_name' => (string) ($team['full_name'] ?? $code),
                'logo' => is_string($team['logo'] ?? null) ? $team['logo'] : null,
                'match_point' => (int) ($row['match_point'] ?? 0),
                'match_wins' => (int) ($matchWl['win'] ?? 0),
                'match_losses' => (int) ($matchWl['lose'] ?? 0),
                'net_game_win' => (int) ($row['net_game_win'] ?? 0),
                'game_wins' => (int) ($gameWl['win'] ?? 0),
                'game_losses' => (int) ($gameWl['lose'] ?? 0),
            ];
        }

        return $out;
    }

    /**
     * Ask the provider to deliver a one-time code to the player's in-game
     * mailbox. No password is involved.
     */
    public function sendVerificationCode(string $roleId, string $zoneId): void
    {
        try {
            $payload = $this->client->postJson(self::NAME, $this->base.'/user/auth/send-vc', [
                'role_id' => (int) $roleId,
                'zone_id' => (int) $zoneId,
            ]);
        } catch (ApiException $exception) {
            if ($exception->payload()['code'] === 'PROVIDER_UNAVAILABLE') {
                // The provider answers 500 (its own response-validation bug)
                // when the upstream rejects the request; surface it as an
                // authentication problem instead of an outage.
                throw ApiException::providerAuth(
                    'The provider could not send a verification code. Check the Player ID and Zone ID.'
                );
            }

            throw $exception;
        }

        if (! $this->client->isSuccess($payload)) {
            throw ApiException::providerAuth($this->client->message(
                $payload,
                'The provider could not send a verification code.'
            ));
        }
    }

    /**
     * Exchange the one-time code for the provider JWT (server-side only).
     */
    public function login(string $roleId, string $zoneId, string $code): string
    {
        try {
            $payload = $this->client->postJson(self::NAME, $this->base.'/user/auth/login', [
                'role_id' => (int) $roleId,
                'zone_id' => (int) $zoneId,
                'vc' => (int) $code,
            ]);
        } catch (ApiException $exception) {
            if ($exception->payload()['code'] === 'PROVIDER_UNAVAILABLE') {
                // Same upstream validation failure as above: an invalid code
                // or account produces a 500 rather than a 401.
                throw ApiException::providerAuth(
                    'Sign-in failed. Check the verification code and try again.'
                );
            }

            throw $exception;
        }

        $data = $this->client->data($payload);
        $token = $data['jwt'] ?? null;

        if (! $this->client->isSuccess($payload) || ! is_string($token) || $token === '') {
            throw ApiException::providerAuth($this->client->message(
                $payload,
                'Sign-in failed. Check the code and try again.'
            ));
        }

        return $token;
    }

    /**
     * Best-effort provider logout; the local session is cleared anyway.
     */
    public function logout(string $token): void
    {
        try {
            $this->client->postJson(self::NAME, $this->base.'/user/auth/logout', [], $token);
        } catch (\Throwable) {
            // Ignored on purpose.
        }
    }

    /**
     * @return array<string, mixed>
     */
    public function userInfo(string $token): array
    {
        $payload = $this->client->getJson(self::NAME, $this->base.'/user/info', ['lang' => 'en'], $token);
        $data = $this->client->data($payload);

        if ($data === null) {
            throw ApiException::providerError("Rone Arena 'user info' payload was malformed.");
        }

        return $data;
    }

    /**
     * @return array<string, mixed>
     */
    public function userStats(string $token): array
    {
        $payload = $this->client->getJson(self::NAME, $this->base.'/user/stats', ['lang' => 'en'], $token);
        $data = $this->client->data($payload);

        if ($data === null) {
            throw ApiException::providerError("Rone Arena 'user stats' payload was malformed.");
        }

        return $data;
    }

    /**
     * @return array{matches: list<array<string, mixed>>, next_cursor: ?string, has_next: bool}
     */
    public function userMatches(string $token, int $limit = 20, ?string $cursor = null): array
    {
        $query = ['limit' => $limit, 'lang' => 'en'];

        if ($cursor !== null && $cursor !== '') {
            $query['last_cursor'] = $cursor;
        }

        $payload = $this->client->getJson(self::NAME, $this->base.'/user/matches', $query, $token);
        $data = $this->client->data($payload);

        if ($data === null) {
            throw ApiException::providerError("Rone Arena 'user matches' payload was malformed.");
        }

        $pageInfo = is_array($data['pageInfo'] ?? null) ? $data['pageInfo'] : [];
        $rows = is_array($data['result'] ?? null) ? $data['result'] : [];
        $matches = [];

        foreach ($rows as $row) {
            $match = $this->parseMatch($row);
            if ($match !== null) {
                $matches[] = $match;
            }
        }

        $nextCursor = $pageInfo['nextCursor'] ?? null;

        return [
            'matches' => $matches,
            'next_cursor' => is_string($nextCursor) && $nextCursor !== '' ? $nextCursor : null,
            'has_next' => (bool) ($pageInfo['hasNext'] ?? false),
        ];
    }

    /**
     * @return list<array<string, mixed>>
     */
    public function userFrequentHeroes(string $token, int $limit = 10): array
    {
        $payload = $this->client->getJson(
            self::NAME,
            $this->base.'/user/heroes/frequent',
            ['limit' => $limit, 'lang' => 'en'],
            $token
        );
        $data = $this->client->data($payload);

        if ($data === null) {
            throw ApiException::providerError("Rone Arena 'frequent heroes' payload was malformed.");
        }

        $rows = is_array($data['result'] ?? null) ? $data['result'] : [];
        $out = [];

        foreach ($rows as $row) {
            if (! is_array($row)) {
                continue;
            }

            $hero = is_array($row['hid_e'] ?? null) ? $row['hid_e'] : [];
            $total = $row['tc'] ?? null;
            $wins = $row['wc'] ?? null;

            $out[] = [
                'hero_id' => $row['hid'] ?? null,
                'hero_name' => $hero['n'] ?? null,
                'hero_icon' => $hero['ix'] ?? null,
                'total_matches' => $total,
                'wins' => $wins,
                'win_rate' => is_int($total) && $total > 0 && is_int($wins) ? $wins / $total : null,
            ];
        }

        return $out;
    }

    /**
     * @return array{id: int, name: string, head_image: ?string, strong_ids: list<int>, weak_ids: list<int>}|null
     */
    private function parseRef(mixed $record): ?array
    {
        if (! is_array($record)) {
            return null;
        }

        $inner = is_array($record['data'] ?? null) ? $record['data'] : [];
        $hero = is_array($inner['hero']['data'] ?? null) ? $inner['hero']['data'] : [];
        $heroId = $inner['hero_id'] ?? null;
        $name = $hero['name'] ?? null;

        if ($heroId === null || ! is_string($name) || $name === '') {
            return null;
        }

        $relation = is_array($inner['relation'] ?? null) ? $inner['relation'] : [];
        $strong = is_array($relation['strong']['target_hero_id'] ?? null) ? $relation['strong']['target_hero_id'] : [];
        $weak = is_array($relation['weak']['target_hero_id'] ?? null) ? $relation['weak']['target_hero_id'] : [];

        return [
            'id' => (int) $heroId,
            'name' => $name,
            'head_image' => is_string($hero['head'] ?? null) ? $hero['head'] : null,
            'strong_ids' => array_values(array_map('intval', array_filter($strong, 'is_int'))),
            'weak_ids' => array_values(array_map('intval', array_filter($weak, 'is_int'))),
        ];
    }

    /**
     * @return array<string, mixed>|null
     */
    private function parseMatch(mixed $row): ?array
    {
        if (! is_array($row)) {
            return null;
        }

        $hero = is_array($row['hid_e'] ?? null) ? $row['hid_e'] : [];
        $kills = (int) ($row['k'] ?? 0);
        $deaths = (int) ($row['d'] ?? 0);
        $assists = (int) ($row['a'] ?? 0);
        $timestamp = $row['ts'] ?? null;
        $playedAt = '';

        if (is_numeric($timestamp) && $timestamp > 0) {
            $seconds = (float) $timestamp;
            if ($seconds > 1_000_000_000_000) {
                $seconds /= 1000;
            }
            $playedAt = gmdate('Y-m-d\TH:i:s\Z', (int) $seconds);
        }

        $battle = $row['bid_s'] ?? $row['bid'] ?? null;

        return [
            'battle_id' => $battle === null ? null : (string) $battle,
            'season_id' => $row['sid'] ?? null,
            'hero_id' => $row['hid'] ?? null,
            'hero_name' => $hero['n'] ?? null,
            'hero_icon' => $hero['ix'] ?? null,
            'kills' => $kills,
            'deaths' => $deaths,
            'assists' => $assists,
            'kda' => round(($kills + $assists) / max($deaths, 1), 2),
            'mvp' => ($row['mvp'] ?? null) === 1,
            'won' => ($row['res'] ?? null) === 1, // provider docs: 1 = win, 0 = loss
            'score' => $row['s'] ?? null,
            'lane_id' => $row['lid'] ?? null,
            'played_at' => $playedAt,
        ];
    }
}
