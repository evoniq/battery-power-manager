$ErrorActionPreference = 'SilentlyContinue'

$root    = Split-Path -Parent $MyInvocation.MyCommand.Path
$server  = Join-Path $root 'nut\mingw64'
$nutRoot = Join-Path $root 'nut\mingw64'
$logDir  = Join-Path $env:ProgramData 'Battery Power Manager\logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Write-Log($msg) {
    $ts = (Get-Date).ToString('yyyy-MM-dd HH:mm:ss')
    "$ts  $msg" | Out-File -FilePath (Join-Path $logDir 'backend.log') -Append -Encoding utf8
}

function Start-IfMissing($name, $exe, $args, $workdir) {
    if (Get-Process -Name $name -ErrorAction SilentlyContinue) {
        Write-Log "$name already running"
        return
    }
    if (-not (Test-Path $exe)) {
        Write-Log "ERROR: $exe not found"
        return
    }
    Write-Log "Starting $name..."
    Start-Process -FilePath $exe -ArgumentList $args -WorkingDirectory $workdir `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDir "$name.out.log") `
        -RedirectStandardError  (Join-Path $logDir "$name.err.log")
}

if (-not (Test-Path $server)) {
    Write-Log "ERROR: NUT directory missing: $server"
    exit 1
}

# NUT resolves etc/ relative to mingw64 root (working directory).
Start-IfMissing 'usbhid-ups' (Join-Path $server 'sbin\usbhid-ups.exe') '-a nutdev1' $nutRoot
Start-Sleep -Seconds 2
Start-IfMissing 'upsd'       (Join-Path $server 'sbin\upsd.exe')       ''           $nutRoot

# Wait until upsd is listening on port 3493 (max 15 seconds)
$ready = $false
for ($i = 0; $i -lt 15; $i++) {
    $conn = Test-NetConnection -ComputerName 127.0.0.1 -Port 3493 `
        -InformationLevel Quiet -WarningAction SilentlyContinue
    if ($conn) { $ready = $true; break }
    Start-Sleep -Seconds 1
}

if ($ready) {
    Write-Log "NUT backend ready on port 3493"
} else {
    Write-Log "WARNING: upsd did not respond on port 3493 after 15s"
}
