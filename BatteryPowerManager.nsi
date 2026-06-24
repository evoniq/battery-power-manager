!define APPNAME "Battery Power Manager"
!define COMPANY "Devon Systems"
!ifndef VERSION
  !define VERSION "0.2.0"
!endif

Name "${APPNAME}"
OutFile "dist\BatteryPowerManagerSetup.exe"
InstallDir "$PROGRAMFILES64\Battery Power Manager"
InstallDirRegKey HKLM "Software\${COMPANY}\${APPNAME}" "InstallDir"
RequestExecutionLevel admin
Unicode true
Icon "installer\assets\battery_power_manager.ico"
UninstallIcon "installer\assets\battery_power_manager.ico"

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
  SetRegView 64
  SetShellVarContext all

  ; Kill any running instances before overwriting files
  ExecWait 'taskkill /F /IM BatteryPowerManager.exe' $0
  ExecWait 'taskkill /F /IM BatteryPowerManagerConsole.exe' $0
  ExecWait 'taskkill /F /IM usbhid-ups.exe' $0
  ExecWait 'taskkill /F /IM upsd.exe' $0
  Sleep 1000

  RMDir /r "$INSTDIR"
  SetOutPath "$INSTDIR"
  File /r "dist\self-contained-installer\BatteryPowerManager\*"
  File /r "dist\self-contained-installer\nut"
  File "dist\self-contained-installer\battery_power_manager.ico"
  File "dist\self-contained-installer\battery_power_manager.png"
  File "installer\Start-BatteryBackend.ps1"

  WriteRegStr HKLM "Software\${COMPANY}\${APPNAME}" "InstallDir" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "BatteryPowerManagerBackend" 'powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "$INSTDIR\Start-BatteryBackend.ps1"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "BatteryPowerManager" '"$INSTDIR\BatteryPowerManager.exe" --tray'

  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BatteryPowerManager" "DisplayName" "${APPNAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BatteryPowerManager" "DisplayVersion" "${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BatteryPowerManager" "Publisher" "${COMPANY}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BatteryPowerManager" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BatteryPowerManager" "DisplayIcon" "$INSTDIR\battery_power_manager.ico"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BatteryPowerManager" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BatteryPowerManager" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BatteryPowerManager" "NoRepair" 1

  CreateDirectory "$SMPROGRAMS\Battery Power Manager"
  CreateShortcut "$SMPROGRAMS\Battery Power Manager\Start Battery Power Manager.lnk" "$INSTDIR\BatteryPowerManager.exe" "--tray" "$INSTDIR\battery_power_manager.ico" 0
  CreateShortcut "$SMPROGRAMS\Battery Power Manager\Battery Power Manager Details.lnk" "$INSTDIR\BatteryPowerManager.exe" "--detail-window" "$INSTDIR\battery_power_manager.ico" 0
  CreateShortcut "$SMPROGRAMS\Battery Power Manager\Test Battery Power Manager Connection.lnk" "$INSTDIR\BatteryPowerManagerConsole.exe" "--once" "$INSTDIR\battery_power_manager.ico" 0
  CreateShortcut "$DESKTOP\Start Battery Power Manager.lnk" "$INSTDIR\BatteryPowerManager.exe" "--tray" "$INSTDIR\battery_power_manager.ico" 0
  CreateShortcut "$DESKTOP\Battery Power Manager Details.lnk" "$INSTDIR\BatteryPowerManager.exe" "--detail-window" "$INSTDIR\battery_power_manager.ico" 0

  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; Start NUT backend and wait until upsd is ready (max 15s)
  ExecShell "open" "powershell.exe" '-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "$INSTDIR\Start-BatteryBackend.ps1"'
  ExecWait 'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "for ($i=0;$i -lt 15;$i++) { if (Test-NetConnection -ComputerName 127.0.0.1 -Port 3493 -InformationLevel Quiet -WarningAction SilentlyContinue) { exit 0 }; Start-Sleep 1 }; exit 1"' $0
  ExecShell "open" "$INSTDIR\BatteryPowerManager.exe" "--tray"
SectionEnd

Section "Uninstall"
  SetRegView 64
  SetShellVarContext all

  ; Stop all running processes before cleanup
  ExecWait 'taskkill /F /IM BatteryPowerManager.exe' $0
  ExecWait 'taskkill /F /IM BatteryPowerManagerConsole.exe' $0
  ExecWait 'taskkill /F /IM usbhid-ups.exe' $0
  ExecWait 'taskkill /F /IM upsd.exe' $0
  Sleep 1000

  DeleteRegValue HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "BatteryPowerManagerBackend"
  DeleteRegValue HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "BatteryPowerManager"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\BatteryPowerManager"
  DeleteRegKey HKLM "Software\${COMPANY}\${APPNAME}"
  Delete "$DESKTOP\Start Battery Power Manager.lnk"
  Delete "$DESKTOP\Battery Power Manager Details.lnk"
  Delete "$SMPROGRAMS\Battery Power Manager\Start Battery Power Manager.lnk"
  Delete "$SMPROGRAMS\Battery Power Manager\Battery Power Manager Details.lnk"
  Delete "$SMPROGRAMS\Battery Power Manager\Test Battery Power Manager Connection.lnk"
  RMDir "$SMPROGRAMS\Battery Power Manager"
  RMDir /r "$INSTDIR"
SectionEnd
