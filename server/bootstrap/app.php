<?php

use App\Exceptions\ApiException;
use App\Http\Middleware\GenerateCspNonce;
use Illuminate\Auth\AuthenticationException;
use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;
use Illuminate\Http\Exceptions\ThrottleRequestsException;
use Illuminate\Http\Request;
use Illuminate\Validation\ValidationException;
use Symfony\Component\HttpKernel\Exception\NotFoundHttpException;

return Application::configure(basePath: dirname(__DIR__))
    ->withRouting(
        web: __DIR__.'/../routes/web.php',
        api: __DIR__.'/../routes/api.php',
        commands: __DIR__.'/../routes/console.php',
        health: '/up',
    )
    ->withMiddleware(function (Middleware $middleware): void {
        // The nonce has to exist before any response is produced, so it is
        // the first middleware in the web group.
        $middleware->prependToGroup('web', GenerateCspNonce::class);
    })
    ->withExceptions(function (Exceptions $exceptions): void {
        $exceptions->shouldRenderJsonWhen(
            fn (Request $request) => $request->is('api/*') || $request->expectsJson(),
        );

        // Typed application errors keep the stable error envelope.
        $exceptions->render(function (ApiException $exception, Request $request) {
            return $exception->render();
        });

        $exceptions->render(function (ValidationException $exception, Request $request) {
            if (! $request->is('api/*')) {
                return null;
            }

            $errors = $exception->errors();

            // Surface the first field error as the message so the app shows
            // "Use 3-24 letters, numbers, underscores, spaces or dots..."
            // instead of a generic "Request validation failed.".
            $firstMessage = collect($errors)->flatten()->first() ?? 'Request validation failed.';

            return response()->json([
                'status' => 'error',
                'code' => 'VALIDATION_ERROR',
                'message' => $firstMessage,
                'details' => json_encode($errors),
                'timestamp' => now()->utc()->format('Y-m-d\TH:i:s.u\Z'),
            ], 422);
        });

        $exceptions->render(function (NotFoundHttpException $exception, Request $request) {
            if (! $request->is('api/*')) {
                return null;
            }

            return response()->json([
                'status' => 'error',
                'code' => 'NOT_FOUND',
                'message' => 'Not found.',
                'timestamp' => now()->utc()->format('Y-m-d\TH:i:s.u\Z'),
            ], 404);
        });

        $exceptions->render(function (ThrottleRequestsException $exception, Request $request) {
            if (! $request->is('api/*')) {
                return null;
            }

            return response()->json([
                'status' => 'error',
                'code' => 'RATE_LIMITED',
                'message' => 'Too many attempts. Wait a minute and try again.',
                'timestamp' => now()->utc()->format('Y-m-d\TH:i:s.u\Z'),
            ], 429);
        });

        $exceptions->render(function (AuthenticationException $exception, Request $request) {
            if (! $request->is('api/*')) {
                return null;
            }

            return ApiException::authRequired()->render();
        });
    })->create();
