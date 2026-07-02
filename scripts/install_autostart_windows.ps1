# Install a Windows Task Scheduler task that starts menisik-daemon natively
# at Windows login using the Windows Python installation.
# Run this from PowerShell (no admin required).
#
# Usage:
#   .\scripts\install_autostart_windows.ps1
#
# To remove:
#   .\scripts\install_autostart_windows.ps1 -Uninstall

param(
    [switch]$Uninstall,
    [string]$PythonExe = ""   # override Python path if needed
)

$TaskName       = "MenisikDaemon"
$LegacyTaskName = "RoverDaemon"
$ProjectDir = "\\wsl.localhost\Ubuntu-20.04\home\nadira\project\menisik"

# ── Uninstall ────────────────────────────────────────────────
if ($Uninstall) {
    Write-Host "Removing Task Scheduler task '$TaskName'..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $LegacyTaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Done." -ForegroundColor Green
    exit 0
}

# ── Locate pythonw.exe ───────────────────────────────────────
if (-not $PythonExe) {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python313\pythonw.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\pythonw.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\pythonw.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\pythonw.exe",
        "C:\Python313\pythonw.exe",
        "C:\Python312\pythonw.exe",
        "C:\Python311\pythonw.exe"
    )
    foreach ($c in $candidates) {
        if (Test-Path $c) { $PythonExe = $c; break }
    }
}

if (-not $PythonExe -or -not (Test-Path $PythonExe)) {
    # Last resort: find python.exe on PATH and swap for pythonw.exe
    $py = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($py) {
        $PythonExe = $py.Source -replace "python\.exe$", "pythonw.exe"
    }
}

if (-not $PythonExe -or -not (Test-Path $PythonExe)) {
    Write-Host "ERROR: pythonw.exe not found." -ForegroundColor Red
    Write-Host "Install Python for Windows or pass -PythonExe 'C:\path\to\pythonw.exe'"
    exit 1
}

Write-Host "Using Python: $PythonExe" -ForegroundColor Cyan

# ── Verify project dir is reachable ─────────────────────────
if (-not (Test-Path $ProjectDir)) {
    Write-Host "WARNING: $ProjectDir not reachable — is WSL running?" -ForegroundColor Yellow
    Write-Host "The task will still be registered and will work once WSL is available."
}

# ── Check dependencies in Windows Python ────────────────────
Write-Host "Checking menisik dependencies in Windows Python..." -ForegroundColor Cyan
$checkCmd = "import importlib.util; missing=[p for p in ['dotenv','httpx'] if importlib.util.find_spec(p) is None]; print(','.join(missing))"
$missing = & $PythonExe -c $checkCmd 2>$null
if ($missing) {
    Write-Host "WARNING: Missing Python packages on Windows: $missing" -ForegroundColor Yellow
    Write-Host "Run to install:" -ForegroundColor Yellow
    Write-Host "  & '$PythonExe' -m pip install -e '$ProjectDir'" -ForegroundColor Yellow
    Write-Host "(Continuing — install packages before the task runs)"
} else {
    Write-Host "Dependencies OK." -ForegroundColor Green
}

# ── Build the action ─────────────────────────────────────────
$action = New-ScheduledTaskAction `
    -Execute          $PythonExe `
    -Argument         "-m src.daemon" `
    -WorkingDirectory $ProjectDir

$trigger  = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 0) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -StartWhenAvailable

# ── Register ─────────────────────────────────────────────────
# Drop the pre-rename task so the daemon is not registered twice.
$legacy = Get-ScheduledTask -TaskName $LegacyTaskName -ErrorAction SilentlyContinue
if ($legacy) {
    Write-Host "Removing legacy task '$LegacyTaskName'..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $LegacyTaskName -Confirm:$false
}

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "Task '$TaskName' already exists — updating..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Register-ScheduledTask `
    -TaskName    $TaskName `
    -Action      $action `
    -Trigger     $trigger `
    -Settings    $settings `
    -RunLevel    Limited `
    -Description "Run menisik-daemon (PR monitor + Telegram bot) natively on Windows at login." `
    | Out-Null

Write-Host ""
Write-Host "Task '$TaskName' registered." -ForegroundColor Green
Write-Host "menisik-daemon will start natively (Windows Python) at every Windows login."
Write-Host ""
Write-Host "To install menisik packages into Windows Python (one time):"
Write-Host "  & '$PythonExe' -m pip install -e '$ProjectDir'"
Write-Host ""
Write-Host "To run it now without restarting:"
Write-Host "  Start-Process '$PythonExe' '-m src.daemon' -WorkingDirectory '$ProjectDir'"
Write-Host ""
Write-Host "To check if it is running:"
Write-Host "  Get-Process pythonw -ErrorAction SilentlyContinue"
Write-Host ""
Write-Host "Logs are written to:"
Write-Host "  $ProjectDir\logs\menisik-daemon.log"
Write-Host ""
Write-Host "To remove this task:"
Write-Host "  .\scripts\install_autostart_windows.ps1 -Uninstall"
