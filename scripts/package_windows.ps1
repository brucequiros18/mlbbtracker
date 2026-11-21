<#
.SYNOPSIS
    Packages MLBB Tracker as a self-contained, downloadable Windows app.

.DESCRIPTION
    Produces releases/MLBB-Tracker-Windows-<version>.zip containing:

      php/                      a bundled PHP 8.4 runtime (no install needed)
      app/                      the Laravel API + built React SPA + vendor/
      START-MLBB-TRACKER.bat    one double-click: migrate + serve + open browser
      README.txt                3-step instructions

    Uses robocopy (multithreaded) and bsdtar - Copy-Item/Compress-Archive are
    far too slow for Laravel's ~50k vendor files.

.PARAMETER Version
    Package version string (default 0.12.0).

.PARAMETER PhpZip
    Path to the PHP Windows zip already downloaded (php-8.4.*-nts-*.zip).
#>
[CmdletBinding()]
param(
    [string]$Version = "0.12.0",
    [string]$PhpZip = "build\php.zip"
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$stage = Join-Path $repoRoot "build\mlbb-tracker"
$phpDir = Join-Path $stage "php"
$appDir = Join-Path $stage "app"
$serverDir = Join-Path $repoRoot "server"
$zipOut = Join-Path $repoRoot "releases\MLBB-Tracker-Windows-$Version.zip"

if (-not (Test-Path $PhpZip)) { throw "PHP zip not found at $PhpZip - download it first." }

# ── Clean stage ────────────────────────────────────────────────────────
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
New-Item -ItemType Directory -Path $phpDir, $appDir -Force | Out-Null

# ── 1. PHP runtime, slimmed ────────────────────────────────────────────
Write-Host "==> Extracting PHP runtime..."
$phpTmp = Join-Path $repoRoot "build\php-extract"
if (Test-Path $phpTmp) { Remove-Item $phpTmp -Recurse -Force }
Expand-Archive -Path $PhpZip -DestinationPath $phpTmp

Copy-Item (Join-Path $phpTmp "php.exe") $phpDir
Copy-Item (Join-Path $phpTmp "php8.dll") $phpDir
robocopy (Join-Path $phpTmp "ext") (Join-Path $phpDir "ext") /E /MT:8 /NFL /NDL /NJH /NJS | Out-Null
Get-ChildItem $phpTmp -Filter "*.dll" | Where-Object {
    $_.Name -match '^(icu|libcrypto|libssl|libssh2|nghttp|zstd|bcrypt)' -or
    $_.Name -in @('libpq.dll','libsodium.dll','gmp.dll')
} | ForEach-Object { Copy-Item $_.FullName $phpDir }
Remove-Item $phpTmp -Recurse -Force

@'
[PHP]
extension_dir = "ext"
extension=curl
extension=openssl
extension=pdo_sqlite
extension=sqlite3
extension=mbstring
extension=fileinfo
extension=zip

memory_limit = 512M
upload_max_filesize = 20M
post_max_size = 25M
'@ | Set-Content (Join-Path $phpDir "php.ini") -Encoding ASCII

# ── 2. Application (API + SPA + vendor) ────────────────────────────────
Write-Host "==> Staging the Laravel app (robocopy /MT:16)..."
foreach ($item in @("app", "bootstrap", "config", "database", "public", "resources", "routes", "storage")) {
    robocopy (Join-Path $serverDir $item) (Join-Path $appDir $item) /E /MT:16 /NFL /NDL /NJH /NJS /NP | Out-Null
}
foreach ($item in @("artisan", "composer.json", "composer.lock", ".env.example")) {
    Copy-Item (Join-Path $serverDir $item) (Join-Path $appDir $item) -Force
}
robocopy (Join-Path $serverDir "vendor") (Join-Path $appDir "vendor") /E /MT:16 /NFL /NDL /NJH /NJS /NP | Out-Null

# The React build (same pipeline as scripts/build_web.ps1).
$dist = Join-Path $repoRoot "web\dist"
if (-not (Test-Path (Join-Path $dist "index.html"))) { throw "web\dist is missing - run scripts\build_web.ps1 first." }
$spaDir = Join-Path $appDir "public\app"
if (Test-Path $spaDir) { Remove-Item $spaDir -Recurse -Force }
robocopy $dist $spaDir /E /MT:16 /NFL /NDL /NJH /NJS /NP | Out-Null

# Ship an EMPTY database: the launcher's `migrate --force` creates the
# tables on first run, so no developer data or test accounts leak into the
# download.
Remove-Item (Join-Path $appDir "database\database.sqlite") -Force -ErrorAction SilentlyContinue
$emptyDb = Join-Path $appDir "database\database.sqlite"
New-Item -ItemType File -Path $emptyDb -Force | Out-Null

# ── 3. Launcher ────────────────────────────────────────────────────────
@'
@echo off
title MLBB Tracker
cd /d "%~dp0app"
set "PATH=%~dp0php;%PATH%"

if not exist .env copy .env.example .env >nul
findstr /C:"APP_KEY=base64" .env >nul 2>&1 || php artisan key:generate --force
php artisan migrate --force

echo.
echo   MLBB Tracker is starting - your browser will open at
echo   http://127.0.0.1:8000
echo   Keep this window open while you use the app. Close it to stop.
echo.
start "" http://127.0.0.1:8000
php artisan serve --host 127.0.0.1 --port 8000
'@ | Set-Content (Join-Path $stage "START-MLBB-TRACKER.bat") -Encoding ASCII

@'
MLBB TRACKER - Windows package
==============================

WHAT THIS IS
  The full MLBB Tracker web app (React front end + Laravel API + database)
  bundled with its own PHP runtime. No installation, no PHP/Composer/Node
  required.

HOW TO RUN
  1. Double-click  START-MLBB-TRACKER.bat
  2. Your browser opens http://127.0.0.1:8000 automatically.
  3. Keep the black window open while using the app; closing it stops the
     server.

REQUIREMENTS
  - Windows 10/11 (64-bit)
  - Internet connection for live hero data and account sign-in

NOTES
  - Your data lives in app\database\database.sqlite (this folder).
  - Uninstall = delete this folder.
  - Unofficial fan project. Not affiliated with Moonton.
'@ | Set-Content (Join-Path $stage "README.txt") -Encoding UTF8

# ── 4. Zip (bsdtar - much faster than Compress-Archive) ───────────────
Write-Host "==> Creating the zip (tar)..."
New-Item -ItemType Directory -Path (Split-Path $zipOut) -Force | Out-Null
if (Test-Path $zipOut) { Remove-Item $zipOut -Force }
tar -a -c -f $zipOut -C $stage .
Write-Host ("==> Done: {0}  ({1:N1} MB)" -f $zipOut, ((Get-Item $zipOut).Length / 1MB))
