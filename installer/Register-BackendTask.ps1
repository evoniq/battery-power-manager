# Registers the NUT backend as a Scheduled Task that runs at logon, but
# delayed 30s so it doesn't contend with WiFi / desktop init during boot.
# Runs the task once immediately after registering.
$ErrorActionPreference = 'Stop'

$here   = Split-Path -Parent $MyInvocation.MyCommand.Path
$script = Join-Path $here 'Start-BatteryBackend.ps1'
$taskName = 'BatteryPowerManagerBackend'

$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -NonInteractive -File `"$script`""

$trigger = New-ScheduledTaskTrigger -AtLogOn
$trigger.Delay = 'PT30S'   # start 30s after logon

$principal = New-ScheduledTaskPrincipal -GroupId 'S-1-5-32-545' -RunLevel Highest  # Users

$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -StartWhenAvailable `
    -ExecutionTimeLimit ([TimeSpan]::Zero)

Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger `
    -Principal $principal -Settings $settings -Force | Out-Null

# Start it now so the user doesn't have to wait for next logon
Start-ScheduledTask -TaskName $taskName
