<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Vite;
use Symfony\Component\HttpFoundation\Response;

/**
 * Generates the per-request Content Security Policy nonce.
 *
 * Laravel's Vite integration exposes the nonce, and Laravel Boost's
 * development browser logger picks it up - that is how an inline script can
 * coexist with a policy that has no `unsafe-inline`.
 *
 * It runs first in the `web` group so the nonce exists before any response
 * (and any injected script) is produced.
 */
class GenerateCspNonce
{
    public function handle(Request $request, Closure $next): Response
    {
        Vite::useCspNonce();

        return $next($request);
    }
}
