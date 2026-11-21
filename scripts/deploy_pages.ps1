<#
.SYNOPSIS
    Builds the React app for GitHub Pages and force-pushes it to gh-pages.

.DESCRIPTION
    GitHub Pages serves static files only, so this deployment pairs the
    built SPA with an API hosted elsewhere (Render - see render.yaml and
    docs/DEPLOY_RENDER.md).

    The result lives at https://<user>.github.io/<repo>/ - here:
    https://brucequiros18.github.io/mlbbtracker/

.PARAMETER ApiBase
    The public origin of the Laravel API, e.g. https://mlbbtracker.onrender.com.
    Empty means same-origin /api/v1 (only useful when the API is unreachable
    and the site shows its honest error states).

.EXAMPLE
    .\scripts\deploy_pages.ps1 -ApiBase https://mlbbtracker.onrender.com
#>
[CmdletBinding()]
param(
    [string]$ApiBase = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$webDir = Join-Path $repoRoot "web"
$pagesBase = "/mlbbtracker/"

Write-Host "==> Building React app for GitHub Pages (base $pagesBase, API: $(if ($ApiBase) { $ApiBase } else { 'same-origin' }))..."
Push-Location $webDir
try {
    $env:VITE_API_BASE = $ApiBase
    npx vite build --base=$pagesBase
    if ($LASTEXITCODE -ne 0) { throw "vite build failed with exit code $LASTEXITCODE." }
} finally {
    Remove-Item Env:\VITE_API_BASE -ErrorAction SilentlyContinue
    Pop-Location
}

$dist = Join-Path $webDir "dist"
if (-not (Test-Path (Join-Path $dist "index.html"))) { throw "Build output missing at $dist." }

Write-Host "==> Fixing absolute paths for the /mlbbtracker/ sub-path..."
$html = Get-Content (Join-Path $dist "index.html") -Raw
$html = $html.Replace('"/app/', '"/mlbbtracker/app/').Replace('"/manifest.webmanifest"', '"/mlbbtracker/manifest.webmanifest"')
Set-Content (Join-Path $dist "index.html") $html -NoNewline

# GitHub Pages serves 404.html for unknown paths - the SPA-fallback trick.
Copy-Item (Join-Path $dist "index.html") (Join-Path $dist "404.html") -Force

$manifestPath = Join-Path $dist "manifest.webmanifest"
if (Test-Path $manifestPath) {
    $manifest = Get-Content $manifestPath -Raw
    $manifest = $manifest.Replace('"start_url": "/"', '"start_url": "/mlbbtracker/"')
    $manifest = $manifest.Replace('"scope": "/"', '"scope": "/mlbbtracker/"')
    $manifest = $manifest.Replace('"/app/icons/', '"/mlbbtracker/app/icons/')
    Set-Content $manifestPath $manifest -NoNewline
}

# The JS bundle references /sw.js (root scope) - GitHub Pages has no
# Service-Worker-Allowed header, so the worker is skipped on Pages; the
# catch() in main.tsx handles it silently.
Write-Host "==> Publishing to the gh-pages branch..."
$tmp = Join-Path $env:TEMP ("mlbb-pages-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tmp | Out-Null
try {
    Copy-Item "$dist\*" $tmp -Recurse -Force
    git -C $tmp init | Out-Null
    git -C $tmp checkout -b gh-pages
    git -C $tmp remote add origin (git -C $repoRoot remote get-url origin)
    git -C $tmp add -A
    git -C $tmp commit -q -m "Pages build $(Get-Date -Format 'yyyy-MM-dd HH:mm') (API: $(if ($ApiBase) { $ApiBase } else { 'same-origin' }))"
    git -C $tmp push -f origin gh-pages
    Write-Host "==> Done. Once Pages is enabled (Settings -> Pages -> branch gh-pages), the app is live at:"
    Write-Host "    https://brucequiros18.github.io/mlbbtracker/"
} finally {
    Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue
}
