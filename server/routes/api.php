<?php

use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\EsportsController;
use App\Http\Controllers\Api\HealthController;
use App\Http\Controllers\Api\HeroController;
use App\Http\Controllers\Api\PlayerController;
use App\Http\Controllers\Api\ReleaseController;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| MLBB Tracker API (v1)
|--------------------------------------------------------------------------
|
| The same JSON contract the Flutter Android app already speaks: one
| response envelope (`data` + `meta`), camelCase keys and a stable error
| `code` on every failure.
|
*/

Route::get('meta', function () {
    return [
        'name' => config('mlbb.app_name'),
        'version' => '1.0.0',
        'api' => config('mlbb.api_v1_prefix'),
        'web' => 'React + Vite single-origin app',
    ];
});

Route::prefix('v1')->group(function (): void {
    Route::prefix('heroes')->group(function (): void {
        Route::get('/', [HeroController::class, 'index']);
        Route::get('rankings', [HeroController::class, 'rankings']);
        Route::get('{identifier}/trends', [HeroController::class, 'trends']);
        Route::get('{identifier}/history', [HeroController::class, 'history']);
        Route::get('{identifier}', [HeroController::class, 'show']);
    });

    Route::get('esports/{league}/standings', [EsportsController::class, 'standings']);

    Route::prefix('players')->group(function (): void {
        Route::post('connect/start', [PlayerController::class, 'connectStart']);
        Route::post('connect/verify', [PlayerController::class, 'connectVerify']);
        Route::post('disconnect', [PlayerController::class, 'disconnect']);
        Route::get('me/profile', [PlayerController::class, 'profile']);
        Route::get('me/stats', [PlayerController::class, 'stats']);
        Route::get('me/matches', [PlayerController::class, 'matches']);
        Route::get('me/heroes', [PlayerController::class, 'heroes']);
        Route::get('{playerId}/{zoneId}', [PlayerController::class, 'lookup']);
    });

    Route::prefix('auth')->group(function (): void {
        Route::get('config', [AuthController::class, 'config']);
        Route::post('firebase', [AuthController::class, 'firebase']);
        Route::post('google', [AuthController::class, 'google']);
        Route::post('register', [AuthController::class, 'register']);
        Route::get('me', [AuthController::class, 'me']);
        Route::patch('me', [AuthController::class, 'updateMe']);
        Route::post('logout', [AuthController::class, 'logout']);
    });

    Route::get('health', [HealthController::class, 'health']);
    Route::get('health/providers', [HealthController::class, 'providers']);
    Route::get('health/history', [HealthController::class, 'history']);

    Route::get('app/release', [ReleaseController::class, 'show']);
});
