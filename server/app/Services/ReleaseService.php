<?php

namespace App\Services;

use Illuminate\Support\Facades\Log;

/**
 * App release manifest and the download page's data.
 *
 * A release is whatever `scripts/package_apk.ps1` published into the
 * releases directory:
 *
 *     releases/
 *     ├── latest.json                    # the manifest (single source of truth)
 *     └── mlbb-tracker-<version>.apk
 *
 * The manifest is read per request (not cached) so publishing a release
 * takes effect immediately without a server restart.
 */
class ReleaseService
{
    public const MANIFEST_NAME = 'latest.json';

    /**
     * The only file names we are ever willing to serve.
     */
    private const APK_NAME = '/^[A-Za-z0-9][A-Za-z0-9._+-]*\.apk$/';

    /**
     * @var list<string>
     */
    private const REQUIRED_KEYS = ['version', 'file', 'size_bytes', 'sha256'];

    /**
     * The directory that holds published releases.
     */
    public function releasesDir(): string
    {
        $configured = trim((string) config('mlbb.releases_dir'));

        if ($configured !== '') {
            return rtrim(str_replace('\\', '/', $configured), '/');
        }

        // Default: <repo>/releases, with this app living in <repo>/server.
        return str_replace('\\', '/', base_path('../releases'));
    }

    /**
     * The directory that holds the built React app.
     */
    public function webRoot(): string
    {
        $configured = trim((string) config('mlbb.web_root'));

        if ($configured !== '') {
            return rtrim(str_replace('\\', '/', $configured), '/');
        }

        return str_replace('\\', '/', public_path('app'));
    }

    /**
     * The published release manifest, or null when nothing is published.
     *
     * A manifest is only accepted when the APK it points at is actually on
     * disk - a manifest without its build would be a broken promise.
     *
     * @return array<string, mixed>|null
     */
    public function readManifest(): ?array
    {
        $path = $this->releasesDir().'/'.self::MANIFEST_NAME;

        if (! is_file($path)) {
            return null;
        }

        $raw = @file_get_contents($path);

        if ($raw === false) {
            return null;
        }

        // utf-8-sig tolerates a BOM (PowerShell's Set-Content adds one).
        $raw = preg_replace('/^\xEF\xBB\xBF/', '', $raw) ?? $raw;
        $data = json_decode($raw, true);

        if (! is_array($data)) {
            Log::warning("release manifest is not valid JSON: {$path}");

            return null;
        }

        foreach (self::REQUIRED_KEYS as $key) {
            if (! array_key_exists($key, $data)) {
                Log::warning("release manifest is missing '{$key}': {$path}");

                return null;
            }
        }

        $fileName = $data['file'];

        if (! is_string($fileName) || preg_match(self::APK_NAME, $fileName) !== 1) {
            Log::warning("release manifest points at an unsafe file name: {$path}");

            return null;
        }

        if ($this->apkPath($fileName) === null) {
            Log::warning("release manifest points at a missing build: {$fileName}");

            return null;
        }

        return $data;
    }

    /**
     * Resolve a requested APK filename safely, or null if not allowed.
     *
     * Only plain `*.apk` names inside the releases directory itself are
     * served - no traversal, no other extensions, no nested paths.
     */
    public function apkPath(string $filename): ?string
    {
        if (preg_match(self::APK_NAME, $filename) !== 1) {
            return null;
        }

        $root = realpath($this->releasesDir());

        if ($root === false) {
            return null;
        }

        $root = str_replace('\\', '/', $root);
        $candidate = realpath($root.'/'.$filename);

        if ($candidate === false) {
            return null;
        }

        $candidate = str_replace('\\', '/', $candidate);

        if (dirname($candidate) !== $root || ! is_file($candidate)) {
            return null;
        }

        return $candidate;
    }

    /**
     * Human-readable file size, or an em dash when the value is unusable.
     */
    public function formatSize(mixed $sizeBytes): string
    {
        if (! is_numeric($sizeBytes)) {
            return '—';
        }

        $size = (float) $sizeBytes;

        if ($size <= 0) {
            return '—';
        }

        return number_format($size / (1024 * 1024), 1).' MB';
    }
}
