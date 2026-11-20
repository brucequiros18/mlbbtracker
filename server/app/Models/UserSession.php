<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

/**
 * A signed-in app session (Google-authenticated).
 *
 * The app holds an opaque bearer token; only its SHA-256 digest is stored
 * here, mirroring the consented player-session pattern.
 */
class UserSession extends Model
{
    /**
     * @var list<string>
     */
    protected $fillable = [
        'token_hash',
        'user_id',
        'expires_at',
        'last_seen_at',
    ];

    /**
     * @return array<string, string>
     */
    protected function casts(): array
    {
        return [
            'expires_at' => 'datetime',
            'last_seen_at' => 'datetime',
        ];
    }

    /**
     * @return BelongsTo<User, $this>
     */
    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }
}
