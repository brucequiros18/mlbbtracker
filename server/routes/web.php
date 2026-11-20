<?php

use App\Http\Controllers\DownloadController;
use App\Http\Controllers\SpaController;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| Web routes
|--------------------------------------------------------------------------
|
| The React + Vite app is served from the same origin as the API, so there
| is no CORS setup and one deployable unit. `/download` stays a plain
| server-rendered page: indexable and functional without JavaScript.
|
*/

Route::get('/download', [DownloadController::class, 'page'])->name('downloads.page');
Route::get('/downloads/{filename}', [DownloadController::class, 'file'])
    ->where('filename', '[A-Za-z0-9._-]+')
    ->name('downloads.show');

// Built assets. Web servers normally serve these straight from `public/`;
// this route is the fallback for hosts that do not.
Route::get('/app/{path}', [SpaController::class, 'asset'])
    ->where('path', '.*')
    ->name('spa.asset');

// The manifest and the service worker live at the origin root so the
// installed app can use `/` as its start URL and scope.
Route::get('/manifest.webmanifest', [SpaController::class, 'manifest'])->name('manifest');
Route::get('/sw.js', [SpaController::class, 'serviceWorker'])->name('service-worker');

Route::get('/{any}', SpaController::class)
    ->where('any', '^(?!api|up|download|downloads|app|manifest\.webmanifest|sw\.js).*$')
    ->name('spa');
