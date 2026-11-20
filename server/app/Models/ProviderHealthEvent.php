<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

/**
 * One observed provider call: reachability, latency and status.
 */
class ProviderHealthEvent extends Model
{
    /**
     * @var list<string>
     */
    protected $fillable = [
        'provider',
        'endpoint',
        'status',
        'status_code',
        'latency_ms',
        'error_code',
        'checked_at',
    ];

    /**
     * @return array<string, string>
     */
    protected function casts(): array
    {
        return [
            'checked_at' => 'datetime',
            'status_code' => 'integer',
            'latency_ms' => 'integer',
        ];
    }
}
