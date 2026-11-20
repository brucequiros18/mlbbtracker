<?php

namespace App\Support;

/**
 * App-only password hashing.
 *
 * The app password is never a sign-in method: Google is. It only confirms
 * changes to the profile, and it never leaves this server.
 */
final class Passwords
{
    public const MIN_LENGTH = 8;

    public const MAX_LENGTH = 128;

    /**
     * Hash a password with the strongest algorithm this PHP build offers.
     */
    public static function hash(string $password): string
    {
        $algorithm = in_array(PASSWORD_ARGON2ID, password_algos(), true)
            ? PASSWORD_ARGON2ID
            : PASSWORD_DEFAULT;

        return password_hash($password, $algorithm);
    }

    /**
     * Check a password against a stored hash, in constant time.
     */
    public static function verify(string $password, ?string $hash): bool
    {
        if ($password === '' || $hash === null || $hash === '') {
            return false;
        }

        return password_verify($password, $hash);
    }
}
