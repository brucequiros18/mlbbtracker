<?php

namespace App\Services;

use App\Exceptions\ApiException;
use App\Models\PlayerSession;
use App\Services\Providers\RoneArenaProvider;
use Illuminate\Support\Facades\Log;

/**
 * Player service.
 *
 * Two capabilities:
 *
 * - `lookup` - anonymous lookup by ID/zone. Still unsupported: no public
 *   source serves another player's stats without their consent.
 * - **connected mode** - the player signs in as themselves with a one-time
 *   code delivered in-game. The provider JWT stays on the server; the app
 *   receives an opaque session key.
 */
class PlayerService
{
    private const UNSUPPORTED_MESSAGE = 'Player statistics require connecting your own account.';

    private const UNSUPPORTED_DETAILS = 'Moonton exposes no public endpoint for another player\'s profile, match history or rank. MLBB Tracker supports a consented sign-in: enter your own Player ID and Zone ID, receive a one-time code in your in-game mailbox, and connect. The backend then reads your real statistics. Anonymous lookups are not supported and nothing is ever fabricated.';

    public function __construct(private readonly RoneArenaProvider $rone) {}

    /**
     * Anonymous lookup is not supported by any permitted source.
     */
    public function lookup(string $playerId, string $zoneId): never
    {
        throw ApiException::notSupported(self::UNSUPPORTED_MESSAGE, self::UNSUPPORTED_DETAILS);
    }

    /**
     * Step 1: ask the provider to deliver a one-time code in-game.
     */
    public function startConnect(string $playerId, string $zoneId): void
    {
        $this->rone->sendVerificationCode($playerId, $zoneId);
    }

    /**
     * Step 2: exchange the code for a provider token and store it server-side.
     *
     * @return array{sessionToken: string, player: array<string, mixed>}
     */
    public function verifyConnect(string $playerId, string $zoneId, string $code): array
    {
        $token = $this->rone->login($playerId, $zoneId, $code);
        $info = $this->rone->userInfo($token);
        $sessionKey = $this->generateSessionKey();

        PlayerSession::query()->create([
            'session_hash' => hash('sha256', $sessionKey),
            'provider_token' => $token,
            'role_id' => (string) ($info['roleId'] ?? $playerId),
            'zone_id' => (string) ($info['zoneId'] ?? $zoneId),
            'ign' => (string) ($info['name'] ?? 'Unknown'),
            'last_seen_at' => now(),
        ]);

        return [
            'sessionToken' => $sessionKey,
            'player' => $this->mapProfile($info),
        ];
    }

    /**
     * Forget the connection (and best-effort end the provider session).
     */
    public function disconnect(string $sessionKey): void
    {
        $row = $this->requireSession($sessionKey);

        try {
            $this->rone->logout($row->provider_token);
        } catch (\Throwable $exception) {
            Log::info('provider logout failed; clearing local session anyway');
        }

        $row->delete();
    }

    /**
     * @return array<string, mixed>
     */
    public function profile(string $sessionKey): array
    {
        return $this->mapProfile($this->rone->userInfo($this->providerToken($sessionKey)));
    }

    /**
     * @return array<string, mixed>
     */
    public function stats(string $sessionKey): array
    {
        $data = $this->rone->userStats($this->providerToken($sessionKey));
        $total = $data['tc'] ?? null;
        $wins = $data['wc'] ?? null;

        return [
            'totalMatches' => is_int($total) ? $total : null,
            'wins' => is_int($wins) ? $wins : null,
            'winRate' => is_int($total) && $total > 0 && is_int($wins) ? $wins / $total : null,
            'avgScore' => isset($data['as']) ? (float) $data['as'] : null,
            'playtimeHours' => isset($data['gt']) ? (float) $data['gt'] : null,
            'mvpCount' => isset($data['mvpc']) ? (int) $data['mvpc'] : null,
            'winStreak' => isset($data['wsc']) ? (int) $data['wsc'] : null,
        ];
    }

    /**
     * @return array{data: list<array<string, mixed>>, nextCursor: ?string, hasNext: bool}
     */
    public function matches(string $sessionKey, int $limit = 20, ?string $cursor = null): array
    {
        $page = $this->rone->userMatches($this->providerToken($sessionKey), $limit, $cursor);
        $matches = array_map(fn (array $match) => $this->mapMatch($match), $page['matches']);

        return [
            'data' => $matches,
            'nextCursor' => $page['next_cursor'],
            'hasNext' => $page['has_next'],
        ];
    }

    /**
     * @return list<array<string, mixed>>
     */
    public function frequentHeroes(string $sessionKey, int $limit = 10): array
    {
        return array_map(fn (array $hero) => [
            'heroId' => $hero['hero_id'],
            'heroName' => $hero['hero_name'],
            'heroIcon' => $hero['hero_icon'],
            'totalMatches' => $hero['total_matches'],
            'wins' => $hero['wins'],
            'winRate' => $hero['win_rate'],
        ], $this->rone->userFrequentHeroes($this->providerToken($sessionKey), $limit));
    }

    /**
     * @param  array<string, mixed>  $info
     * @return array<string, mixed>
     */
    private function mapProfile(array $info): array
    {
        return [
            'playerId' => (string) ($info['roleId'] ?? ''),
            'zoneId' => (string) ($info['zoneId'] ?? ''),
            'ign' => (string) ($info['name'] ?? 'Unknown'),
            'avatar' => $info['avatar'] ?? null,
            'level' => isset($info['level']) ? (int) $info['level'] : null,
            'rankLevel' => isset($info['rank_level']) ? (int) $info['rank_level'] : null,
            'rankName' => null,
            'rankIcon' => null,
            'totalMatches' => null,
            'wins' => null,
            'losses' => null,
            'winRate' => null,
            'kda' => null,
            'mvpCount' => null,
        ];
    }

    /**
     * @param  array<string, mixed>  $match
     * @return array<string, mixed>
     */
    private function mapMatch(array $match): array
    {
        return [
            'battleId' => $match['battle_id'],
            'seasonId' => $match['season_id'],
            'heroId' => $match['hero_id'],
            'heroName' => $match['hero_name'],
            'heroIcon' => $match['hero_icon'],
            'kills' => $match['kills'],
            'deaths' => $match['deaths'],
            'assists' => $match['assists'],
            'kda' => $match['kda'],
            'mvp' => $match['mvp'],
            'won' => $match['won'],
            'score' => $match['score'],
            'laneId' => $match['lane_id'],
            'playedAt' => $match['played_at'],
        ];
    }

    private function providerToken(string $sessionKey): string
    {
        $row = $this->requireSession($sessionKey);

        $row->forceFill(['last_seen_at' => now()])->save();

        return $row->provider_token;
    }

    private function requireSession(string $sessionKey): PlayerSession
    {
        $row = PlayerSession::query()
            ->where('session_hash', hash('sha256', $sessionKey))
            ->first();

        if ($row === null) {
            throw ApiException::providerAuth('Session not found. Please connect your account again.');
        }

        return $row;
    }

    private function generateSessionKey(): string
    {
        return rtrim(strtr(base64_encode(random_bytes(32)), '+/', '-_'), '=');
    }
}
