$ErrorActionPreference = 'SilentlyContinue'

$root    = Split-Path -Parent $MyInvocation.MyCommand.Path
$mingw   = Join-Path $root 'nut\mingw64'
$logDir  = Join-Path $env:ProgramData 'Battery Power Manager\logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Write-Log($msg) {
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    "$ts  $msg" | Out-File -FilePath (Join-Path $logDir 'backend.log') -Append -Encoding utf8
}

# Hidden startup info: SW_HIDE so the console apps run with no visible window.
$startup = ([WMIClass]"Win32_ProcessStartup").CreateInstance()
$startup.ShowWindow = 0  # SW_HIDE
$wmiProc = [WMIClass]"Win32_Process"

# Spawn fully detached AND hidden. Win32_Process.Create parents the process to
# WmiPrvSE so it survives this launcher (and the installer) exiting, and the
# SW_HIDE startup info keeps the console window invisible.
function Start-Detached($name, $exe, $cmdline, $workdir) {
    if (Get-Process -Name $name -ErrorAction SilentlyContinue) {
        Write-Log "$name already running"; return
    }
    if (-not (Test-Path $exe)) { Write-Log "ERROR: $exe not found"; return }
    Write-Log "Starting $name (detached, hidden)..."
    $r = $wmiProc.Create($cmdline, $workdir, $startup)
    if ($r.ReturnValue -ne 0) { Write-Log "ERROR: $name failed (rv=$($r.ReturnValue))" }
    else { Write-Log "$name started pid=$($r.ProcessId)" }
}

if (-not (Test-Path $mingw)) { Write-Log "ERROR: NUT missing: $mingw"; exit 1 }

# NUT for Windows mingw64 build: drivers in bin\, daemons in sbin\.
# CurrentDirectory = mingw64 so etc\ups.conf is resolved.
Start-Detached 'usbhid-ups' "$mingw\bin\usbhid-ups.exe" "`"$mingw\bin\usbhid-ups.exe`" -a nutdev1" $mingw
Start-Sleep -Seconds 3
Start-Detached 'upsd' "$mingw\sbin\upsd.exe" "`"$mingw\sbin\upsd.exe`"" $mingw

# Wait until upsd is listening (max 15s). Use a lightweight TcpClient probe
# instead of Test-NetConnection, which is heavy and slow at logon time.
$ready = $false
for ($i = 0; $i -lt 15; $i++) {
    try {
        $c = New-Object System.Net.Sockets.TcpClient
        $c.Connect('127.0.0.1', 3493)
        $c.Close()
        $ready = $true; break
    } catch { Start-Sleep -Seconds 1 }
}
if ($ready) { Write-Log "NUT ready on port 3493" } else { Write-Log "WARNING: upsd timeout" }
