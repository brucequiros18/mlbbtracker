<?php

namespace App\Models;

use Database\Factories\UserFactory;
use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;

/**
 * An app account, created by signing in with Google or Firebase.
 *
 * A row carries whichever credential created it: `google_sub` (the stable
 * subject of a verified Google ID token) or `firebase_uid` (the stable UID of
 * a verified Firebase ID token). Either way that subject - never the email -
 * is the identity key.
 *
 * `username`, `mlbb_id` and `password_hash` are app-only profile data:
 *
 * - the MLBB ID is self-declared and never verified against Moonton;
 * - the password is a salted Argon2id hash that never leaves this database.
 *   It is not a sign-in method and is never sent to Moonton - it only
 *   confirms changes to the profile (see PATCH /api/v1/auth/me).
 */
class User extends Model
{
    /** @use HasFactory<UserFactory> */
    use HasFactory;

    /**
     * @var list<string>
     */
    protected $fillable = [
        'google_sub',
        'firebase_uid',
        'email',
        'email_verified',
        'google_name',
        'picture_url',
        'username',
        'mlbb_id',
        'password_hash',
        'last_login_at',
    ];

    /**
     * @var list<string>
     */
    protected $hidden = [
        'password_hash',
    ];

    /**
     * @return array<string, string>
     */
    protected function casts(): array
    {
        return [
            'email_verified' => 'boolean',
            'last_login_at' => 'datetime',
        ];
    }

    /**
     * Whether the player completed username, MLBB ID and app password.
     */
    public function hasCompleteProfile(): bool
    {
        return $this->username !== null
            && $this->mlbb_id !== null
            && $this->password_hash !== null;
    }
}
