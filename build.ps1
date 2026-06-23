# Build script for Battery Power Manager
# Usage: .\build.ps1
# Requirements: Python + uv, PyInstaller, NSIS, NUT Windows binaries

param(
    [string]$NutDir = "nut",          # path to NUT Windows binaries folder
    [string]$Version = "0.2.0"
)

$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
$Dist = Join-Path $Root "dist\self-contained-installer"

Write-Host "=== Battery Power Manager Build ===" -ForegroundColor Cyan
Write-Host "Version: $Version"
Write-Host "Output:  $Dist"

# --- 1. Clean dist ---
if (Test-Path $Dist) { Remove-Item -Recurse -Force $Dist }
New-Item -ItemType Directory -Force -Path $Dist | Out-Null

# --- 2. Install Python deps ---
Write-Host "`n[1/5] Installing Python dependencies..." -ForegroundColor Yellow
uv sync --extra build --extra tray
if ($LASTEXITCODE -ne 0) { throw "uv sync failed" }

# --- 3. PyInstaller - GUI tray app (no console window) ---
Write-Host "`n[2/5] Building BatteryPowerManager.exe (tray, no console)..." -ForegroundColor Yellow
uv run pyinstaller `
    --onedir `
    --noconsole `
    --name BatteryPowerManager `
    --icon installer\assets\battery_power_manager.ico `
    --add-data "src\ecoflow_tray\assets\*;ecoflow_tray\assets" `
    --distpath "$Dist" `
    --noconfirm `
    src\ecoflow_tray\cli.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller (GUI) failed" }

# --- 4. PyInstaller - Console diagnostic tool ---
Write-Host "`n[3/5] Building BatteryPowerManagerConsole.exe (console)..." -ForegroundColor Yellow
uv run pyinstaller `
    --onedir `
    --console `
    --name BatteryPowerManagerConsole `
    --icon installer\assets\battery_power_manager.ico `
    --distpath "$Root\dist\_console_tmp" `
    --noconfirm `
    src\ecoflow_tray\cli.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller (console) failed" }
# Move console exe into the main BatteryPowerManager folder so NSIS packs one dir
Copy-Item "$Root\dist\_console_tmp\BatteryPowerManagerConsole\BatteryPowerManagerConsole.exe" `
    "$Dist\BatteryPowerManager\" -Force

# --- 5. Bundle NUT binaries ---
Write-Host "`n[4/5] Bundling NUT backend..." -ForegroundColor Yellow
$NutSource = if ([System.IO.Path]::IsPathRooted($NutDir)) { $NutDir } else { Join-Path $Root $NutDir }
if (-not (Test-Path $NutSource)) {
    Write-Warning "NUT directory not found at: $NutSource"
    Write-Warning "Download NUT for Windows from https://github.com/networkupstools/nut/releases"
    Write-Warning "Expected structure: $NutSource\x86_64-w64-mingw32-nut-server\sbin\upsc.exe"
} else {
    Copy-Item -Recurse -Force $NutSource "$Dist\nut"
    Write-Host "  NUT binaries copied from $NutSource"
}

# --- 6. Copy assets ---
Write-Host "`n[5/5] Copying assets..." -ForegroundColor Yellow
Copy-Item "installer\assets\battery_power_manager.ico" "$Dist\"
Copy-Item "installer\assets\battery_power_manager.png" "$Dist\"

# --- 7. Build NSIS installer ---
$Makensis = Get-Command makensis -ErrorAction SilentlyContinue
if ($Makensis) {
    Write-Host "`n[6/6] Building NSIS installer..." -ForegroundColor Yellow
    makensis /DVERSION=$Version BatteryPowerManager.nsi
    if ($LASTEXITCODE -ne 0) { throw "NSIS build failed" }
    Write-Host "`nInstaller: dist\BatteryPowerManagerSetup.exe" -ForegroundColor Green
} else {
    Write-Warning "makensis not found — skipping installer. Install NSIS from https://nsis.sourceforge.io"
    Write-Host "dist\self-contained-installer\ is ready for manual NSIS build." -ForegroundColor Yellow
}

Write-Host "`nBuild complete!" -ForegroundColor Green
