$ErrorActionPreference = 'SilentlyContinue'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$server = Join-Path $root 'nut\x86_64-w64-mingw32-nut-server'
$nutRoot = Join-Path $root 'nut'
$logDir = Join-Path $env:ProgramData 'Battery Power Manager\logs'
New-Item -ItemType Directory -Force -Path $logDir | Out-Null

function Start-IfMissing($name, $exe, $args, $workdir) {
    if (Get-Process -Name $name -ErrorAction SilentlyContinue) { return }
    Start-Process -FilePath $exe -ArgumentList $args -WorkingDirectory $workdir -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logDir "$name.out.log") -RedirectStandardError (Join-Path $logDir "$name.err.log")
}

if (-not (Test-Path $server)) {
    "NUT directory missing: $server" | Out-File -FilePath (Join-Path $logDir 'backend.err.log') -Append -Encoding utf8
    exit 1
}

# NUT for Windows resolves etc/ relative to the parent folder containing
# x86_64-w64-mingw32-nut-server. Do not start from the server/sbin directory.
Start-IfMissing 'usbhid-ups' (Join-Path $server 'sbin\usbhid-ups.exe') '-a nutdev1' $nutRoot
Start-Sleep -Seconds 2
Start-IfMissing 'upsd' (Join-Path $server 'sbin\upsd.exe') '' $nutRoot
