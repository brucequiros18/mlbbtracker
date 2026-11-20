# Builds the React app and copies it to Laravel's public/app directory.
#
# The Laravel app serves the bundle from the origin root: the HTML comes
# from public/app/index.html and its assets from public/app/assets/.
#
# Usage: .\scripts\build_web.ps1 [-Clean]

param(
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$webDir = Join-Path $repoRoot "web"
$laravelPublic = Join-Path $repoRoot "server\public\app"

Write-Host "==> Building React app..."
Push-Location $webDir
try {
    if ($Clean) {
        Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
    }
    npm run build
    if ($LASTEXITCODE -ne 0) {
        throw "npm run build failed with exit code $LASTEXITCODE."
    }
} finally {
    Pop-Location
}

if (-not (Test-Path (Join-Path $webDir "dist"))) {
    Write-Error "Build output not found at $webDir\dist"
}

Write-Host "==> Copying build to Laravel public directory..."
if (Test-Path $laravelPublic) {
    # Remove the old build first: hashed asset names change on every build
    # and stale files would otherwise pile up forever.
    Remove-Item -Path "$laravelPublic\*" -Recurse -Force -ErrorAction SilentlyContinue
} else {
    New-Item -ItemType Directory -Path $laravelPublic -Force | Out-Null
}

Get-ChildItem -Path "$webDir\dist\*" -Force | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $laravelPublic -Recurse -Force
}

Write-Host "==> Build complete. The React app is served at / by the Laravel app."
