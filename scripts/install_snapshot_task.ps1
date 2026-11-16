<#
.SYNOPSIS
    Installs (or removes) a Windows Task Scheduler job that records the daily
    MLBB meta snapshot.

.DESCRIPTION
    The recorded-history chart in the app only grows if something records a
    snapshot every day. This task runs `backend/scripts/record_snapshot.py`,
    which is idempotent: one row per hero per UTC day, so a missed run or a
    manual re-run can never duplicate data.

    The task runs as the current user, whether or not they are logged on
    (the password is never stored).

.PARAMETER Time
    Local time of day for the daily run. Default 03:15.

.PARAMETER Uninstall
    Remove the task instead of creating it.

.PARAMETER RunNow
    Also record a snapshot immediately, so history starts today.

.EXAMPLE
    .\scripts\install_snapshot_task.ps1 -RunNow

.EXAMPLE
    .\scripts\install_snapshot_task.ps1 -Uninstall
#>
[CmdletBinding()]
param(
    [string]$Time = '03:15',
    [switch]$Uninstall,
    [switch]$RunNow
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot 'backend'
$python = Join-Path $backendDir '.venv\Scripts\python.exe'
$script = Join-Path $backendDir 'scripts\record_snapshot.py'
$taskName = 'MLBB Tracker - Daily Snapshot'
$logFile = Join-Path $backendDir 'snapshot_task.log'

function Remove-SnapshotTask {
    if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
        Write-Host "Removed scheduled task '$taskName'."
    } else {
        Write-Host "No scheduled task named '$taskName'."
    }
}

if ($Uninstall) {
    Remove-SnapshotTask
    return
}

# — Preconditions ————————————————————————————————————————————————
if (-not (Test-Path $python)) {
    throw "Python venv not found at $python. Create it first: cd backend; py -m venv .venv"
}
if (-not (Test-Path $script)) {
    throw "Snapshot script not found at $script."
}

$parsed = [datetime]::ParseExact($Time, 'HH:mm', $null)
$trigger = New-ScheduledTaskTrigger -Daily -At $parsed

$action = New-ScheduledTaskAction `
    -Execute $python `
    -Argument "scripts\record_snapshot.py" `
    -WorkingDirectory $backendDir

# Run whether or not the user is logged on; never store a password.
$principal = New-ScheduledTaskPrincipal `
    -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive `
    -RunLevel Limited

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 15) `
    -RestartCount 2 `
    -RestartInterval (New-TimeSpan -Minutes 10)

if (Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
}

Register-ScheduledTask `
    -TaskName $taskName `
    -Description 'Records one daily MLBB meta snapshot per hero (idempotent, one row per UTC day).' `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings | Out-Null

Write-Host "Installed scheduled task '$taskName'."
Write-Host "  Runs daily at : $Time (local time)"
Write-Host "  Command       : $python scripts\record_snapshot.py"
Write-Host "  Working dir   : $backendDir"

# — Optionally run it once now, so the first snapshot exists immediately ————
if ($RunNow) {
    Push-Location $backendDir
    try {
        # The snapshot script logs to stderr; keep that from being treated as
        # a terminating error and judge success by the exit code instead.
        $previousPreference = $ErrorActionPreference
        $ErrorActionPreference = 'Continue'
        & $python 'scripts\record_snapshot.py'
        $exitCode = $LASTEXITCODE
        $ErrorActionPreference = $previousPreference
        if ($exitCode -ne 0) {
            Write-Warning "The snapshot script exited with code $exitCode."
        }
    } finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "Task list entry:"
Get-ScheduledTask -TaskName $taskName |
    Select-Object TaskName, State |
    Format-Table -AutoSize
