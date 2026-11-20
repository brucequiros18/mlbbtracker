<?php

namespace Tests\Fakes;

use App\Services\Providers\MlbbdexProvider;

/**
 * An MLBBDex adapter that never touches the network.
 */
class FakeMlbbdexProvider extends MlbbdexProvider
{
    public function __construct()
    {
        // The real constructor only reads the configured base URL.
    }

    /**
     * @return list<array{slug: string, name: string, roles: list<string>, lanes: list<string>, specialties: list<string>}>
     */
    public function fetchHeroCatalog(): array
    {
        return [
            [
                'slug' => 'khufra',
                'name' => 'Khufra',
                'roles' => ['Tank'],
                'lanes' => ['Roam'],
                'specialties' => ['Control'],
            ],
            [
                'slug' => 'masha',
                'name' => 'Masha',
                'roles' => ['Fighter', 'Tank'],
                'lanes' => ['Exp'],
                'specialties' => ['Push'],
            ],
            [
                'slug' => 'balmond',
                'name' => 'Balmond',
                'roles' => ['Tank'],
                'lanes' => ['Exp'],
                'specialties' => ['Push'],
            ],
            [
                'slug' => 'ruby',
                'name' => 'Ruby',
                'roles' => ['Support'],
                'lanes' => ['Gold'],
                'specialties' => ['Burst'],
            ],
        ];
    }

    /**
     * @return array{slug: string, name: string, roles: list<string>, lanes: list<string>, specialties: list<string>, skills: list<array{name: string, description: string}>, stats: array<string, string>}
     */
    public function fetchHeroDetail(string $slug): array
    {
        return [
            'slug' => $slug,
            'name' => ucfirst($slug),
            'roles' => ['Tank'],
            'lanes' => ['Roam'],
            'specialties' => ['Control'],
            'skills' => [
                [
                    'name' => 'Spell Curse',
                    'description' => 'Curses the target with damage over time.',
                ],
            ],
            'stats' => ['Win rate' => '51.23%'],
        ];
    }

    /**
     * @return list<array{id: ?int, name: string, slug: ?string, head_image: ?string, win_rate: float, ban_rate: float, pick_rate: float, tier: ?string}>
     */
    public function fetchRankings(): array
    {
        return [
            [
                'id' => null,
                'name' => 'Khufra',
                'slug' => 'khufra',
                'head_image' => null,
                'win_rate' => 0.5123,
                'ban_rate' => 0.2211,
                'pick_rate' => 0.0334,
                'tier' => 'A+',
            ],
            [
                'id' => null,
                'name' => 'Masha',
                'slug' => 'masha',
                'head_image' => null,
                'win_rate' => 0.5846,
                'ban_rate' => 0.4190,
                'pick_rate' => 0.0487,
                'tier' => 'S+',
            ],
        ];
    }

    /**
     * @return list<array{version: string, title: string, link: string}>
     */
    public function fetchPatches(): array
    {
        return [];
    }
}
