<?php

namespace App\Http\Controllers;

use App\Services\ReleaseService;
use App\Support\Csp;
use Illuminate\Contracts\View\View;
use Illuminate\Http\Request;
use Illuminate\Http\Response;
use Symfony\Component\HttpFoundation\BinaryFileResponse;

/**
 * Serves the React + Vite single-page app.
 *
 * The build lives in `public/app` (copied from `web/dist`). Every unknown
 * path falls through to `index.html` so client-side routing works on a
 * hard refresh. When no build exists yet the app says so honestly instead
 * of serving a broken page.
 */
class SpaController extends Controller
{
    /**
     * The browser-facing policy for the app shell.
     *
     * Scripts and styles come from this origin plus Google's Identity
     * Services (the sign-in button) and Google Fonts. Images may come from
     * anywhere, because hero portraits are served by third-party providers.
     */
    public function __invoke(Request $request, ReleaseService $releases): View|Response
    {
        $index = $releases->webRoot().'/index.html';

        if (! is_file($index)) {
            return response()->view('web-missing', [], 503)
                ->header('Cache-Control', 'no-store');
        }

        return response()
            ->view('spa', ['indexHtml' => (string) file_get_contents($index)])
            ->header('Cache-Control', 'no-store')
            ->header('Content-Security-Policy', Csp::header(Csp::app()));
    }

    /**
     * Serve a built asset (JS, CSS, icons, images).
     *
     * Web servers usually hand these straight off from `public/`; this route
     * is the fallback so the app also works where that is not configured.
     */
    public function asset(Request $request, string $path, ReleaseService $releases): BinaryFileResponse
    {
        $file = $this->shellFile($path, $releases);

        if ($file === null) {
            abort(404);
        }

        return response()->file($file, [
            'Cache-Control' => 'public, max-age=31536000, immutable',
        ]);
    }

    /**
     * The web app manifest, served from the origin root so its `start_url`
     * and `scope` can be `/`.
     */
    public function manifest(ReleaseService $releases): BinaryFileResponse
    {
        $file = $this->shellFile('manifest.webmanifest', $releases);

        if ($file === null) {
            abort(404);
        }

        return response()->file($file, [
            'Content-Type' => 'application/manifest+json',
            'Cache-Control' => 'public, max-age=3600',
        ]);
    }

    /**
     * The service worker.
     *
     * It lives at the origin root so its scope covers the whole app, which
     * is why the `Service-Worker-Allowed` header is sent as well.
     */
    public function serviceWorker(ReleaseService $releases): BinaryFileResponse
    {
        $file = $this->shellFile('sw.js', $releases);

        if ($file === null) {
            abort(404);
        }

        return response()->file($file, [
            'Content-Type' => 'application/javascript',
            'Cache-Control' => 'no-cache',
            'Service-Worker-Allowed' => '/',
        ]);
    }

    /**
     * Resolve a path inside the built app, refusing anything that escapes it.
     */
    private function shellFile(string $path, ReleaseService $releases): ?string
    {
        $root = realpath($releases->webRoot());

        if ($root === false) {
            return null;
        }

        $root = str_replace('\\', '/', $root);
        $candidate = realpath($root.'/'.$path);

        if ($candidate === false) {
            return null;
        }

        $candidate = str_replace('\\', '/', $candidate);

        if (! str_starts_with($candidate, $root.'/') || ! is_file($candidate)) {
            return null;
        }

        return $candidate;
    }
}
