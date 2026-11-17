<#
.SYNOPSIS
    Build the Flutter web app and serve it together with the API.

.DESCRIPTION
    Produces a single-origin web deployment:
      1. `flutter build web --release --no-web-resources-cdn` -> mobile/build/web
      2. FastAPI serves the API *and* the static build, so the app and the API
         share an origin (no CORS configuration required).

    `--no-web-resources-cdn` bundles CanvasKit with the app instead of loading
    it from gstatic, so the installable PWA still paints offline.

    The app is then available at http://127.0.0.1:8000/
    (API docs at http://127.0.0.1:8000/docs, download page at /download).

.EXAMPLE
    .\scripts\run_web.ps1
    .\scripts\run_web.ps1 -Port 8080 -Rebuild
#>
param(
    [int]$Port = 8000,
    [string]$HostAddress = "127.0.0.1",
    [switch]$Rebuild
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$webDir = Join-Path $repoRoot "mobile\build\web"

if ($Rebuild -or -not (Test-Path (Join-Path $webDir "index.html"))) {
    Write-Host "==> Building Flutter web release..."
    Push-Location (Join-Path $repoRoot "mobile")
    try { flutter build web --release --no-web-resources-cdn } finally { Pop-Location }
} else {
    Write-Host "==> Using existing build in mobile\build\web (pass -Rebuild to rebuild)"
}

if (-not (Test-Path (Join-Path $webDir "index.html"))) {
    Write-Error "Web build not found at $webDir"
}

Write-Host "==> Serving API + web app on http://${HostAddress}:$Port/"
Push-Location (Join-Path $repoRoot "backend")
try {
    .\.venv\Scripts\python.exe -m uvicorn app.main:app --host $HostAddress --port $Port
} finally {
    Pop-Location
}
