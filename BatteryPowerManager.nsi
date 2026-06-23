!define APPNAME "Battery Power Manager"
!define COMPANY "Devon Systems"
!define VERSION "0.1.0"

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
  RMDir /r "$INSTDIR"
  SetOutPath "$INSTDIR"
  File /r "dist\self-contained-installer\BatteryPowerManager\*"
  File "dist\self-contained-installer\battery_power_manager.ico"
  File "dist\self-contained-installer\battery_power_manager.png"

  WriteRegStr HKLM "Software\${COMPANY}\${APPNAME}" "InstallDir" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "BatteryPowerManager" '"$INSTDIR\BatteryPowerManager.exe" --tray'

  CreateDirectory "$SMPROGRAMS\Battery Power Manager"
  CreateShortcut "$SMPROGRAMS\Battery Power Manager\Start Battery Power Manager.lnk" "$INSTDIR\BatteryPowerManager.exe" "--tray" "$INSTDIR\battery_power_manager.ico" 0
  CreateShortcut "$SMPROGRAMS\Battery Power Manager\Battery Power Manager Details.lnk" "$INSTDIR\BatteryPowerManager.exe" "--detail-window" "$INSTDIR\battery_power_manager.ico" 0
  CreateShortcut "$SMPROGRAMS\Battery Power Manager\Test Battery Power Manager Connection.lnk" "$INSTDIR\BatteryPowerManagerConsole.exe" "--once" "$INSTDIR\battery_power_manager.ico" 0
  CreateShortcut "$DESKTOP\Start Battery Power Manager.lnk" "$INSTDIR\BatteryPowerManager.exe" "--tray" "$INSTDIR\battery_power_manager.ico" 0
  CreateShortcut "$DESKTOP\Battery Power Manager Details.lnk" "$INSTDIR\BatteryPowerManager.exe" "--detail-window" "$INSTDIR\battery_power_manager.ico" 0

  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ExecShell "open" "$INSTDIR\BatteryPowerManager.exe" "--tray"
SectionEnd

Section "Uninstall"
  SetRegView 64
  SetShellVarContext all
  DeleteRegValue HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "BatteryPowerManager"
  DeleteRegKey HKLM "Software\${COMPANY}\${APPNAME}"
  Delete "$DESKTOP\Start Battery Power Manager.lnk"
  Delete "$DESKTOP\Battery Power Manager Details.lnk"
  Delete "$SMPROGRAMS\Battery Power Manager\Start Battery Power Manager.lnk"
  Delete "$SMPROGRAMS\Battery Power Manager\Battery Power Manager Details.lnk"
  Delete "$SMPROGRAMS\Battery Power Manager\Test Battery Power Manager Connection.lnk"
  RMDir "$SMPROGRAMS\Battery Power Manager"
  RMDir /r "$INSTDIR"
SectionEnd
