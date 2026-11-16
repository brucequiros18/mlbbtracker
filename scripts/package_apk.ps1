<#
.SYNOPSIS
    Builds the Android APK and publishes it for the /download page.

.DESCRIPTION
    Builds the Flutter APK, copies it into `releases/`, computes its SHA-256,
    reads the real minSdk from the artifact (via aapt2), and writes
    `releases/latest.json` - the single source of truth the backend's
    `/download` page and `/api/v1/app/release` read.

    Until a release keystore is configured, Flutter signs release builds with
    the debug keys; the manifest says so honestly.

.PARAMETER Notes
    Release notes, one per line. Shown under "What's new" on the page.

.PARAMETER SkipBuild
    Publish the existing APK without rebuilding.

.PARAMETER DebugBuild
    Package a debug APK instead of a release APK.

.EXAMPLE
    .\scripts\package_apk.ps1 -Notes "Download page`nRecorded history chart"
#>
[CmdletBinding()]
param(
    [string]$Notes = '',
    [switch]$SkipBuild,
    [switch]$DebugBuild
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$mobileDir = Join-Path $repoRoot 'mobile'
$releasesDir = Join-Path $repoRoot 'releases'
$pubspec = Join-Path $mobileDir 'pubspec.yaml'

if (-not (Test-Path $pubspec)) {
    throw "pubspec.yaml not found at $pubspec."
}

# - Version from pubspec (versionName+buildNumber) ----------------
$match = Select-String -Path $pubspec -Pattern '^version:\s*(.+)$'
if (-not $match) { throw "No 'version:' line in $pubspec." }
$versionLine = $match.Matches[0].Groups[1].Value.Trim()
$versionName = ($versionLine -split '\+')[0]
$buildNumber = ($versionLine -split '\+')[-1]

$apkName = if ($DebugBuild) { 'app-debug.apk' } else { 'app-release.apk' }
$apkSource = Join-Path $mobileDir "build\app\outputs\flutter-apk\$apkName"

# - Build --------------------------------------------------------
if (-not $SkipBuild) {
    Push-Location $mobileDir
    try {
        if ($DebugBuild) { flutter build apk --debug } else { flutter build apk --release }
        if ($LASTEXITCODE -ne 0) { throw "flutter build apk failed with exit code $LASTEXITCODE." }
    } finally {
        Pop-Location
    }
}

if (-not (Test-Path $apkSource)) {
    throw "APK not found at $apkSource (build first, or drop -SkipBuild)."
}

# - Publish ------------------------------------------------------
New-Item -ItemType Directory -Force -Path $releasesDir | Out-Null
$fileName = "mlbb-tracker-$versionName.apk"
$destination = Join-Path $releasesDir $fileName
Copy-Item -Path $apkSource -Destination $destination -Force

$sha256 = (Get-FileHash -Path $destination -Algorithm SHA256).Hash.ToLowerInvariant()
$sizeBytes = (Get-Item $destination).Length

# - minSdk read from the artifact itself ------------------------
$minAndroid = 'unknown'
$aapt2 = Get-ChildItem "$env:LOCALAPPDATA\Android\Sdk\build-tools" -Directory -ErrorAction SilentlyContinue |
    Sort-Object Name -Descending |
    ForEach-Object { Join-Path $_.FullName 'aapt2.exe' } |
    Where-Object { Test-Path $_ } |
    Select-Object -First 1

if ($aapt2) {
    $badging = & $aapt2 dump badging $destination 2>$null
    $sdkLine = $badging | Select-String -Pattern "sdkVersion:'(\d+)'" | Select-Object -First 1
    if ($sdkLine) {
        $api = [int]$sdkLine.Matches[0].Groups[1].Value
        $androidNames = @{
            21 = '5.0'; 22 = '5.1'; 23 = '6.0'; 24 = '7.0'; 25 = '7.1'; 26 = '8.0';
            27 = '8.1'; 28 = '9'; 29 = '10'; 30 = '11'; 31 = '12'; 32 = '12L';
            33 = '13'; 34 = '14'; 35 = '15'; 36 = '16'
        }
        $name = $androidNames[$api]
        $minAndroid = if ($name) { "$name (API $api)" } else { "API $api" }
    }
}

$signedWith = if ($DebugBuild) {
    'debug build'
} else {
    'debug keys - preview build; configure a release keystore before store distribution'
}

$noteLines = @()
if ($Notes) {
    $noteLines = @($Notes -split "`r?`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ })
} else {
    # Republishing without -Notes keeps the notes already in the manifest.
    $existing = Join-Path $releasesDir 'latest.json'
    if (Test-Path $existing) {
        try {
            $previous = Get-Content $existing -Raw | ConvertFrom-Json
            if ($previous.notes) { $noteLines = @($previous.notes) }
        } catch {
            # A corrupt manifest is simply replaced.
        }
    }
}

$manifest = [ordered]@{
    version      = $versionLine
    version_name = $versionName
    build        = [int]$buildNumber
    channel      = if ($DebugBuild) { 'debug' } else { 'preview' }
    file         = $fileName
    size_bytes   = $sizeBytes
    sha256       = $sha256
    released_at  = (Get-Date).ToUniversalTime().ToString('yyyy-MM-dd')
    min_android  = $minAndroid
    signed_with  = $signedWith
    notes        = $noteLines
}

$manifestPath = Join-Path $releasesDir 'latest.json'
$json = $manifest | ConvertTo-Json -Depth 4
# Write without a BOM: PowerShell's `-Encoding UTF8` adds one on 5.1, and a
# BOM breaks strict JSON parsers.
[System.IO.File]::WriteAllText(
    $manifestPath,
    $json,
    (New-Object System.Text.UTF8Encoding($false))
)

# - Summary ------------------------------------------------------
$sizeMb = [math]::Round($sizeBytes / 1MB, 1)
Write-Host ""
Write-Host "Published release $versionLine"
Write-Host "  APK       : $destination ($sizeMb MB)"
Write-Host "  SHA-256   : $sha256"
Write-Host "  Min SDK   : $minAndroid"
Write-Host "  Manifest  : $manifestPath"
Write-Host ""
Write-Host "Served at /download (restart not required - the manifest is read per request)."
