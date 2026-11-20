<?php

namespace Tests\Fakes;

use App\Exceptions\ApiException;
use App\Services\Providers\RoneArenaProvider;

/**
 * A Rone Arena adapter that never touches the network.
 *
 * It serves the same shapes as the real adapter so the service layer and
 * the API can be tested end to end, offline.
 */
class FakeRoneArenaProvider extends RoneArenaProvider
{
    public int $sentCodes = 0;

    public int $logouts = 0;

    public function __construct()
    {
        // The real constructor only reads the configured base URL.
    }

    /**
     * @return list<array{id: int, name: string, head_image: ?string, strong_ids: list<int>, weak_ids: list<int>}>
     */
    public function fetchHeroRefs(): array
    {
        return [
            [
                'id' => 78,
                'name' => 'Khufra',
                'head_image' => 'https://img.example/khufra.png',
                'strong_ids' => [7],
                'weak_ids' => [99],
            ],
            [
                'id' => 88,
                'name' => 'Masha',
                'head_image' => 'https://img.example/masha.png',
                'strong_ids' => [],
                'weak_ids' => [],
            ],
            [
                'id' => 7,
                'name' => 'Balmond',
                'head_image' => 'https://img.example/balmond.png',
                'strong_ids' => [],
                'weak_ids' => [],
            ],
            [
                'id' => 99,
                'name' => 'Ruby',
                'head_image' => 'https://img.example/ruby.png',
                'strong_ids' => [],
                'weak_ids' => [],
            ],
        ];
    }

    /**
     * @return list<array{id: ?int, name: string, slug: ?string, head_image: ?string, win_rate: float, ban_rate: float, pick_rate: float, tier: ?string}>
     */
    public function fetchRankings(int $days, string $rank, string $sortField): array
    {
        return [
            [
                'id' => 88,
                'name' => 'Masha',
                'slug' => null,
                'head_image' => 'https://img.example/masha.png',
                'win_rate' => 0.5846,
                'ban_rate' => 0.4190,
                'pick_rate' => 0.0487,
                'tier' => 'S+',
            ],
            [
                'id' => 78,
                'name' => 'Khufra',
                'slug' => null,
                'head_image' => 'https://img.example/khufra.png',
                'win_rate' => 0.5123,
                'ban_rate' => 0.2211,
                'pick_rate' => 0.0334,
                'tier' => 'A+',
            ],
        ];
    }

    /**
     * @return list<array{date: string, win_rate: float, ban_rate: float, pick_rate: float}>
     */
    public function fetchTrends(int $heroId, int $days): array
    {
        return [
            [
                'date' => '2026-01-01',
                'win_rate' => 0.5000,
                'ban_rate' => 0.2000,
                'pick_rate' => 0.0300,
            ],
            [
                'date' => '2026-01-02',
                'win_rate' => 0.5123,
                'ban_rate' => 0.2211,
                'pick_rate' => 0.0334,
            ],
        ];
    }

    /**
     * @return list<array{rank: int, team_code: string, team_name: string, logo: ?string, match_point: int, match_wins: int, match_losses: int, net_game_win: int, game_wins: int, game_losses: int}>
     */
    public function fetchStandings(string $league): array
    {
        return [
            [
                'rank' => 1,
                'team_code' => 'TLID',
                'team_name' => 'TEAM LIQUID ID',
                'logo' => 'https://img.example/tlid.png',
                'match_point' => 12,
                'match_wins' => 12,
                'match_losses' => 4,
                'net_game_win' => 15,
                'game_wins' => 26,
                'game_losses' => 11,
            ],
            [
                'rank' => 2,
                'team_code' => 'NAVI',
                'team_name' => 'NAVI',
                'logo' => null,
                'match_point' => 12,
                'match_wins' => 12,
                'match_losses' => 4,
                'net_game_win' => 12,
                'game_wins' => 25,
                'game_losses' => 12,
            ],
        ];
    }

    public function sendVerificationCode(string $roleId, string $zoneId): void
    {
        if ($roleId === '999999999') {
            throw ApiException::providerAuth(
                'The provider could not send a verification code. Check the Player ID and Zone ID.'
            );
        }

        $this->sentCodes++;
    }

    public function login(string $roleId, string $zoneId, string $code): string
    {
        if ($code !== '111111') {
            throw ApiException::providerAuth(
                'Sign-in failed. Check the verification code and try again.'
            );
        }

        return 'provider-jwt-for-'.$roleId;
    }

    public function logout(string $token): void
    {
        $this->logouts++;
    }

    /**
     * @return array<string, mixed>
     */
    public function userInfo(string $token): array
    {
        return [
            'roleId' => 123456789,
            'zoneId' => 1234,
            'name' => 'Ash',
            'avatar' => 'https://img.example/avatar.png',
            'level' => 42,
        ];
    }

    /**
     * @return array<string, mixed>
     */
    public function userStats(string $token): array
    {
        return [
            'tc' => 100,
            'wc' => 55,
            'as' => 8.5,
            'gt' => 120.25,
            'mvpc' => 9,
            'wsc' => 4,
        ];
    }

    /**
     * @return array{matches: list<array<string, mixed>>, next_cursor: ?string, has_next: bool}
     */
    public function userMatches(string $token, int $limit = 20, ?string $cursor = null): array
    {
        return [
            'matches' => [
                [
                    'battle_id' => 'battle-1',
                    'season_id' => 12,
                    'hero_id' => 78,
                    'hero_name' => 'Khufra',
                    'hero_icon' => 'https://img.example/khufra.png',
                    'kills' => 5,
                    'deaths' => 2,
                    'assists' => 9,
                    'kda' => 7.0,
                    'mvp' => true,
                    'won' => true,
                    'score' => 1234,
                    'lane_id' => 3,
                    'played_at' => '2026-01-02T10:00:00Z',
                ],
            ],
            'next_cursor' => null,
            'has_next' => false,
        ];
    }

    /**
     * @return list<array<string, mixed>>
     */
    public function userFrequentHeroes(string $token, int $limit = 10): array
    {
        return [
            [
                'hero_id' => 78,
                'hero_name' => 'Khufra',
                'hero_icon' => 'https://img.example/khufra.png',
                'total_matches' => 40,
                'wins' => 22,
                'win_rate' => 0.55,
            ],
        ];
    }
}
