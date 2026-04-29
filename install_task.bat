@echo off
setlocal
:: install_task.bat — registers Task Scheduler jobs for the contribution engine
:: Run as Administrator
::
:: Logic:
::   - Morning task: 09:03 daily
::   - Evening task: 21:03 daily
::   - Both tasks use "Run task as soon as possible after a scheduled start is missed"
::     so if PC was off at 09:03, it runs immediately on next startup.

set "SCRIPT=%~dp0run.bat"
set "TASK_PREFIX=GitHubContributionEngine"

echo Installing GitHub Contribution Engine scheduled tasks...
echo.

:: --- Morning: 09:03 ---
schtasks /delete /tn "%TASK_PREFIX%_Morning" /f >nul 2>&1

powershell -NoProfile -Command ^
  "$action = New-ScheduledTaskAction -Execute '%SCRIPT%';" ^
  "$trigger = New-ScheduledTaskTrigger -Daily -At '09:03AM';" ^
  "$trigger.StartBoundary = [DateTime]::Today.AddHours(9).AddMinutes(3).ToString('s');" ^
  "$settings = New-ScheduledTaskSettingsSet -RunOnlyIfNetworkAvailable -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2);" ^
  "Register-ScheduledTask -TaskName '%TASK_PREFIX%_Morning' -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -Force | Out-Null;" ^
  "Write-Host '[OK] Morning task registered (09:03, runs on startup if missed)'"

if %errorlevel% neq 0 goto :error

:: --- Evening: 21:03 ---
schtasks /delete /tn "%TASK_PREFIX%_Evening" /f >nul 2>&1

powershell -NoProfile -Command ^
  "$action = New-ScheduledTaskAction -Execute '%SCRIPT%';" ^
  "$trigger = New-ScheduledTaskTrigger -Daily -At '09:03PM';" ^
  "$trigger.StartBoundary = [DateTime]::Today.AddHours(21).AddMinutes(3).ToString('s');" ^
  "$settings = New-ScheduledTaskSettingsSet -RunOnlyIfNetworkAvailable -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2);" ^
  "Register-ScheduledTask -TaskName '%TASK_PREFIX%_Evening' -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -Force | Out-Null;" ^
  "Write-Host '[OK] Evening task registered (21:03, runs on startup if missed)'"

if %errorlevel% neq 0 goto :error

echo.
echo Done. Both tasks will run on startup if PC was off at scheduled time.
echo To verify:  schtasks /query /tn "%TASK_PREFIX%_Morning" /v /fo LIST
echo To remove:  schtasks /delete /tn "%TASK_PREFIX%_Morning" /f
echo             schtasks /delete /tn "%TASK_PREFIX%_Evening" /f
goto :end

:error
echo.
echo ERROR: Run this script as Administrator.
exit /b 1

:end
pause
