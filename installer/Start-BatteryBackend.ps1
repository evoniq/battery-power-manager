$ErrorActionPreference = 'SilentlyContinue'

$root    = Split-Path -Parent $MyInvocation.MyCommand.Path
$mingw   = Join-Path $root 'nut\mingw64'
$logDir  = Join-Path $env:ProgramData 'Battery Power Manager\logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Write-Log($msg) {
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    "$ts  $msg" | Out-File -FilePath (Join-Path $logDir 'backend.log') -Append -Encoding utf8
}

function Start-IfMissing($name, $exe, $args, $workdir) {
    if (Get-Process -Name $name -ErrorAction SilentlyContinue) {
        Write-Log "$name already running"; return
    }
    if (-not (Test-Path $exe)) { Write-Log "ERROR: $exe not found"; return }
    Write-Log "Starting $name..."
    Start-Process -FilePath $exe -ArgumentList $args -WorkingDirectory $workdir `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDir "$name.out.log") `
        -RedirectStandardError  (Join-Path $logDir "$name.err.log")
}

if (-not (Test-Path $mingw)) { Write-Log "ERROR: NUT missing: $mingw"; exit 1 }

# NUT for Windows mingw64 build: drivers in bin\, daemons in sbin\.
# Working directory = mingw64 so etc\ups.conf is resolved.
Start-IfMissing 'usbhid-ups' (Join-Path $mingw 'bin\usbhid-ups.exe') '-a nutdev1' $mingw
Start-Sleep -Seconds 3
Start-IfMissing 'upsd' (Join-Path $mingw 'sbin\upsd.exe') '' $mingw

# Wait until upsd is listening (max 15s)
$ready = $false
for ($i = 0; $i -lt 15; $i++) {
    if (Test-NetConnection -ComputerName 127.0.0.1 -Port 3493 -InformationLevel Quiet -WarningAction SilentlyContinue) {
        $ready = $true; break
    }
    Start-Sleep -Seconds 1
}
if ($ready) { Write-Log "NUT ready on port 3493" } else { Write-Log "WARNING: upsd timeout" }
