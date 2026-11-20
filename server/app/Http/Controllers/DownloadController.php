<?php

namespace App\Http\Controllers;

use App\Services\ReleaseService;
use App\Support\Csp;
use Illuminate\Contracts\View\View;
use Illuminate\Http\Request;
use Illuminate\Http\Response;
use Symfony\Component\HttpFoundation\BinaryFileResponse;

/**
 * The `/download` landing page and the published APK files.
 *
 * The page is plain server-rendered HTML: indexable, fast, and it works
 * without JavaScript. A missing release renders an honest "not published
 * yet" state instead of a broken link.
 */
class DownloadController extends Controller
{
    public function page(ReleaseService $releases): View|Response
    {
        $manifest = $releases->readManifest();

        return response()
            ->view('download', [
                'manifest' => $manifest,
                'fileName' => is_array($manifest) ? (string) $manifest['file'] : null,
                'size' => is_array($manifest) ? $releases->formatSize($manifest['size_bytes'] ?? null) : '—',
                'sha256' => is_array($manifest) ? (string) ($manifest['sha256'] ?? '') : '',
            ])
            ->header('Cache-Control', 'no-store')
            ->header('Content-Security-Policy', Csp::header(Csp::download()));
    }

    public function file(Request $request, string $filename, ReleaseService $releases): BinaryFileResponse
    {
        $path = $releases->apkPath($filename);

        if ($path === null) {
            abort(404);
        }

        return response()->download(
            $path,
            $filename,
            ['Content-Type' => 'application/vnd.android.package-archive']
        );
    }
}
