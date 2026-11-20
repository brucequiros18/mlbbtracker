<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

/**
 * Persistent provider-response cache (cold tier behind the cache store).
 */
class ApiCacheEntry extends Model
{
    /**
     * @var list<string>
     */
    protected $fillable = [
        'cache_key',
        'provider',
        'payload',
        'expires_at',
    ];

    /**
     * @return array<string, string>
     */
    protected function casts(): array
    {
        return [
            'payload' => 'array',
            'expires_at' => 'datetime',
        ];
    }
}
