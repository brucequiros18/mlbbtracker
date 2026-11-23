<#
.SYNOPSIS
    Builds the React app and publishes BOTH sites to GitHub Pages:
    the download/landing page (site/) at the root and the SPA under /app/.

.DESCRIPTION
    GitHub Pages serves static files only, so this deployment pairs the
    built SPA with an API hosted elsewhere (Render - see render.yaml and
    docs/DEPLOYMENT.md).

    The result lives at https://<user>.github.io/<repo>/ - here:
      https://brucequiros18.github.io/mlbbtracker/        landing page (site/)
      https://brucequiros18.github.io/mlbbtracker/app/    React SPA demo

    The root 404.html is the SPA index, so deep links such as
    /mlbbtracker/app/compare?h=masha,argus keep working (GitHub Pages
    serves 404.html for unknown paths - the SPA-fallback trick).

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
$siteDir = Join-Path $repoRoot "site"
$pagesBase = "/mlbbtracker/app/"

if (-not (Test-Path (Join-Path $siteDir "index.html"))) {
    throw "Landing page missing at $siteDir\index.html."
}

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

Write-Host "==> Fixing absolute paths for the /mlbbtracker/app/ sub-path..."
$html = Get-Content (Join-Path $dist "index.html") -Raw
$html = $html.Replace('"/app/', '"/mlbbtracker/app/').Replace('"/manifest.webmanifest"', '"/mlbbtracker/app/manifest.webmanifest"')
Set-Content (Join-Path $dist "index.html") $html -NoNewline

$manifestPath = Join-Path $dist "manifest.webmanifest"
if (Test-Path $manifestPath) {
    $manifest = Get-Content $manifestPath -Raw
    $manifest = $manifest.Replace('"start_url": "/"', '"start_url": "/mlbbtracker/app/"')
    $manifest = $manifest.Replace('"scope": "/"', '"scope": "/mlbbtracker/app/"')
    $manifest = $manifest.Replace('"/app/icons/', '"/mlbbtracker/app/icons/')
    Set-Content $manifestPath $manifest -NoNewline
}

# Assemble the Pages tree: landing page at the root, SPA under app/.
Write-Host "==> Assembling Pages tree (site/ -> root, dist -> app/)..."
$tmp = Join-Path $env:TEMP ("mlbb-pages-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tmp | Out-Null
try {
    Copy-Item "$siteDir\*" $tmp -Recurse -Force
    $appDir = Join-Path $tmp "app"
    New-Item -ItemType Directory -Path $appDir | Out-Null
    Copy-Item "$dist\*" $appDir -Recurse -Force

    # GitHub Pages serves 404.html for unknown paths - the SPA-fallback trick.
    # The root 404 is the SPA index, prefixed with a redirect that folds any
    # unknown path under the app's basename - React Router v7 renders nothing
    # when a URL does not start with the basename, so /mlbbtracker/<page>
    # becomes /mlbbtracker/app/<page> (and the app shows its own 404).
    $appIndex = Get-Content (Join-Path $dist "index.html") -Raw
    $redirect = @"
<script>
// Fold unknown paths under the app basename so the router can match them.
(function () {
  var p = location.pathname;
  if (p.indexOf("/mlbbtracker/app/") !== 0 && p !== "/mlbbtracker/app") {
    location.replace("/mlbbtracker/app/" + p.replace(/^\/mlbbtracker\/?/, "") + location.search);
  }
})();
</script>
"@
    $appIndex = $appIndex -replace "(?i)</head>", "$redirect`n</head>"
    Set-Content (Join-Path $tmp "404.html") $appIndex -NoNewline

    git -C $tmp init | Out-Null
    git -C $tmp checkout -b gh-pages
    git -C $tmp remote add origin (git -C $repoRoot remote get-url origin)
    git -C $tmp add -A
    git -C $tmp commit -q -m "Pages build $(Get-Date -Format 'yyyy-MM-dd HH:mm') (landing + app, API: $(if ($ApiBase) { $ApiBase } else { 'same-origin' }))"
    git -C $tmp push -f origin gh-pages
    Write-Host "==> Done. Once Pages is enabled (Settings -> Pages -> branch gh-pages), the sites are live at:"
    Write-Host "    https://brucequiros18.github.io/mlbbtracker/        (download page)"
    Write-Host "    https://brucequiros18.github.io/mlbbtracker/app/    (web app demo)"
} finally {
    Remove-Item $tmp -Recurse -Force
}
