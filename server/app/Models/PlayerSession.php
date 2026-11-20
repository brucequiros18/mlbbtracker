<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

/**
 * A consented player connection.
 *
 * The provider JWT is stored server-side only; the app holds an opaque
 * session key whose SHA-256 hash is what appears in `session_hash`.
 */
class PlayerSession extends Model
{
    /**
     * @var list<string>
     */
    protected $fillable = [
        'session_hash',
        'provider_token',
        'role_id',
        'zone_id',
        'ign',
        'last_seen_at',
    ];

    /**
     * @return array<string, string>
     */
    protected function casts(): array
    {
        return [
            'last_seen_at' => 'datetime',
        ];
    }
}
