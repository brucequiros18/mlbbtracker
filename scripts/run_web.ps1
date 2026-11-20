<#
.SYNOPSIS
    Serve the Laravel API with the React web app.

.DESCRIPTION
    Produces a single-origin web deployment:
      1. Builds React app (web/) using Vite
      2. Copies build to server/public/app/
      3. Laravel serves the API and static build

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
$webDir = Join-Path $repoRoot "web"
$laravelPublic = Join-Path $repoRoot "server\public\app"

if ($Rebuild -or -not (Test-Path (Join-Path $laravelPublic "index.html"))) {
    Write-Host "==> Building React web app..."
    Push-Location $webDir
    try {
        npm install --silent 2>$null
        npm run build
    } finally {
        Pop-Location
    }
} else {
    Write-Host "==> Using existing build in server\public\app (pass -Rebuild to rebuild)"
}

if (-not (Test-Path (Join-Path $laravelPublic "index.html"))) {
    Write-Error "Web build not found at $laravelPublic"
}

Write-Host "==> Starting Laravel development server on http://${HostAddress}:$Port/"
Push-Location (Join-Path $repoRoot "server")
try {
    php artisan serve --host=$HostAddress --port=$Port
} finally {
    Pop-Location
}