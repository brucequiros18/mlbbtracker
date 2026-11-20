<?php

namespace App\Support;

use Illuminate\Support\Facades\Vite;

/**
 * Content Security Policy helpers.
 *
 * The policies are strict: no `unsafe-inline` for scripts. The one inline
 * script that can appear is Laravel Boost's development browser logger, and
 * it is allowed through a per-request nonce.
 */
final class Csp
{
    /**
     * The policy for the React app shell.
     *
     * Scripts and styles come from this origin plus Google's Identity
     * Services (the sign-in button) and Google Fonts. Images may come from
     * anywhere, because hero portraits are served by third-party providers.
     *
     * @return array<string, list<string>>
     */
    public static function app(): array
    {
        return [
            'default-src' => ["'self'"],
            'script-src' => self::scripts(["'self'", 'https://accounts.google.com']),
            'style-src' => ["'self'", "'unsafe-inline'", 'https://fonts.googleapis.com'],
            'font-src' => ["'self'", 'https://fonts.gstatic.com', 'data:'],
            'img-src' => ["'self'", 'data:', 'https:'],
            'connect-src' => ["'self'", 'https://accounts.google.com'],
            'frame-src' => ['https://accounts.google.com'],
            'worker-src' => ["'self'"],
            'manifest-src' => ["'self'"],
            'base-uri' => ["'self'"],
            'form-action' => ["'self'"],
            'frame-ancestors' => ["'none'"],
        ];
    }

    /**
     * The policy for the server-rendered download page.
     *
     * @return array<string, list<string>>
     */
    public static function download(): array
    {
        return [
            'default-src' => ["'none'"],
            'script-src' => self::scripts(["'self'"]),
            'style-src' => ["'self'", "'unsafe-inline'"],
            'img-src' => ["'self'", 'data:', 'https:'],
            'connect-src' => ["'self'"],
            'manifest-src' => ["'self'"],
            'worker-src' => ["'self'"],
            'base-uri' => ["'none'"],
            'form-action' => ["'none'"],
            'frame-ancestors' => ["'none'"],
        ];
    }

    /**
     * The script source list, plus the per-request nonce when one exists.
     *
     * @param  list<string>  $sources
     * @return list<string>
     */
    private static function scripts(array $sources): array
    {
        $nonce = Vite::cspNonce();

        if (is_string($nonce) && $nonce !== '') {
            $sources[] = "'nonce-".$nonce."'";
        }

        return $sources;
    }

    /**
     * Render a policy as a header value.
     *
     * @param  array<string, list<string>>  $directives
     */
    public static function header(array $directives): string
    {
        $parts = [];

        foreach ($directives as $directive => $sources) {
            $parts[] = $directive.' '.implode(' ', $sources);
        }

        return implode('; ', $parts);
    }
}
