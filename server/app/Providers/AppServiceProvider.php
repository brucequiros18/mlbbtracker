<?php

namespace App\Providers;

use App\Services\AuthService;
use App\Services\FirebaseTokenVerifier;
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

        // The verifiers need their credentials (OAuth client ID / Firebase
        // project ID), which may legitimately be empty on a fresh checkout.
        // They are only resolvable when configured.
        $this->app->bind(GoogleTokenVerifier::class, function (): GoogleTokenVerifier {
            $clientId = (string) config('mlbb.google_client_id');

            if ($clientId === '') {
                throw new \RuntimeException(
                    'Google sign-in is not configured. Set MLBB_GOOGLE_CLIENT_ID.'
                );
            }

            return new GoogleTokenVerifier($clientId);
        });

        $this->app->bind(FirebaseTokenVerifier::class, function (): FirebaseTokenVerifier {
            $projectId = (string) config('mlbb.firebase_project_id');

            if ($projectId === '') {
                throw new \RuntimeException(
                    'Firebase sign-in is not configured. Set MLBB_FIREBASE_PROJECT_ID.'
                );
            }

            return new FirebaseTokenVerifier($projectId);
        });

        // AuthService takes optional verifiers: with no credentials configured
        // it reports the honest "not configured" state instead of failing to
        // resolve.
        $this->app->bind(AuthService::class, function ($app): AuthService {
            $clientId = (string) config('mlbb.google_client_id');
            $projectId = (string) config('mlbb.firebase_project_id');

            $googleVerifier = $clientId === ''
                ? null
                : $app->make(GoogleTokenVerifier::class);

            $firebaseVerifier = $projectId === ''
                ? null
                : $app->make(FirebaseTokenVerifier::class);

            return new AuthService($googleVerifier, $firebaseVerifier);
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
