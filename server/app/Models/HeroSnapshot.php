<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

/**
 * A daily observation of a hero's rank-window statistics.
 */
class HeroSnapshot extends Model
{
    /**
     * @var list<string>
     */
    protected $fillable = [
        'hero_id',
        'hero_name',
        'days',
        'captured_on',
        'win_rate',
        'ban_rate',
        'pick_rate',
        'tier',
        'rank_position',
    ];

    /**
     * @return array<string, string>
     */
    protected function casts(): array
    {
        return [
            'captured_on' => 'date',
            'win_rate' => 'float',
            'ban_rate' => 'float',
            'pick_rate' => 'float',
            'rank_position' => 'integer',
        ];
    }
}
