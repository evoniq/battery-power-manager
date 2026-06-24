$ErrorActionPreference = 'SilentlyContinue'

$root    = Split-Path -Parent $MyInvocation.MyCommand.Path
$mingw   = Join-Path $root 'nut\mingw64'
$logDir  = Join-Path $env:ProgramData 'Battery Power Manager\logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Write-Log($msg) {
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    "$ts  $msg" | Out-File -FilePath (Join-Path $logDir 'backend.log') -Append -Encoding utf8
}

# Spawn a process fully detached from this script via the WMI provider.
# Win32_Process.Create parents the new process to WmiPrvSE, so it survives
# this launcher (and the installer/scheduled-task) exiting — unlike
# Start-Process children, which Windows tears down with the parent.
function Start-Detached($name, $exe, $cmdline, $workdir) {
    if (Get-Process -Name $name -ErrorAction SilentlyContinue) {
        Write-Log "$name already running"; return $true
    }
    if (-not (Test-Path $exe)) { Write-Log "ERROR: $exe not found"; return $false }
    Write-Log "Starting $name (detached)..."
    $res = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
        CommandLine      = $cmdline
        CurrentDirectory = $workdir
    }
    if ($res.ReturnValue -ne 0) { Write-Log "ERROR: failed to start $name (rv=$($res.ReturnValue))"; return $false }
    return $true
}

if (-not (Test-Path $mingw)) { Write-Log "ERROR: NUT missing: $mingw"; exit 1 }

# NUT for Windows mingw64 build: drivers in bin\, daemons in sbin\.
# CurrentDirectory = mingw64 so etc\ups.conf is resolved.
Start-Detached 'usbhid-ups' "$mingw\bin\usbhid-ups.exe" "`"$mingw\bin\usbhid-ups.exe`" -a nutdev1" $mingw
Start-Sleep -Seconds 3
Start-Detached 'upsd' "$mingw\sbin\upsd.exe" "`"$mingw\sbin\upsd.exe`"" $mingw

# Wait until upsd is listening (max 15s)
$ready = $false
for ($i = 0; $i -lt 15; $i++) {
    if (Test-NetConnection -ComputerName 127.0.0.1 -Port 3493 -InformationLevel Quiet -WarningAction SilentlyContinue) {
        $ready = $true; break
    }
    Start-Sleep -Seconds 1
}
if ($ready) { Write-Log "NUT ready on port 3493" } else { Write-Log "WARNING: upsd timeout" }
