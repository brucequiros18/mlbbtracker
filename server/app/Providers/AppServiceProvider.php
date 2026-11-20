<?php

namespace App\Providers;

use App\Services\AuthService;
use App\Services\GoogleTokenVerifier;
use App\Services\ProviderHealthRecorder;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    /**
     * Register any application services.
     */
    public function register(): void
    {
        $this->app->singleton(ProviderHealthRecorder::class);

        // The verifier needs the OAuth client ID, which may legitimately be
        // empty on a fresh checkout. It is only resolvable when configured.
        $this->app->bind(GoogleTokenVerifier::class, function (): GoogleTokenVerifier {
            $clientId = (string) config('mlbb.google_client_id');

            if ($clientId === '') {
                throw new \RuntimeException(
                    'Google sign-in is not configured. Set MLBB_GOOGLE_CLIENT_ID.'
                );
            }

            return new GoogleTokenVerifier($clientId);
        });

        // AuthService takes an optional verifier: with no client ID configured
        // it reports the honest "not configured" state instead of failing to
        // resolve.
        $this->app->bind(AuthService::class, function ($app): AuthService {
            $clientId = (string) config('mlbb.google_client_id');

            $verifier = $clientId === ''
                ? null
                : $app->make(GoogleTokenVerifier::class);

            return new AuthService($verifier);
        });
    }

    /**
     * Bootstrap any application services.
     */
    public function boot(): void
    {
        //
    }
}
