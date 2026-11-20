<?php

namespace App\Services;

use App\Services\Providers\RoneArenaProvider;
use Illuminate\Support\Facades\Cache;

/**
 * Esports service: professional league standings (MPL ID/PH/MY/KH).
 */
class EsportsService
{
    /**
     * The leagues the provider exposes.
     *
     * @var list<string>
     */
    public const LEAGUES = ['id', 'ph', 'my', 'kh'];

    public function __construct(private readonly RoneArenaProvider $rone) {}

    /**
     * @return list<array{rank: int, teamCode: string, teamName: string, logo: ?string, matchPoint: int, matchWins: int, matchLosses: int, netGameWin: int, gameWins: int, gameLosses: int}>
     */
    public function standings(string $league): array
    {
        $key = "esports:v1:{$league}";

        $cached = Cache::get($key);
        if (is_array($cached)) {
            return $cached;
        }

        $rows = array_map(
            fn (array $row) => [
                'rank' => $row['rank'],
                'teamCode' => $row['team_code'],
                'teamName' => $row['team_name'],
                'logo' => $row['logo'],
                'matchPoint' => $row['match_point'],
                'matchWins' => $row['match_wins'],
                'matchLosses' => $row['match_losses'],
                'netGameWin' => $row['net_game_win'],
                'gameWins' => $row['game_wins'],
                'gameLosses' => $row['game_losses'],
            ],
            $this->rone->fetchStandings($league)
        );

        Cache::put($key, $rows, (int) config('mlbb.cache_ttl_rankings'));

        return $rows;
    }
}
