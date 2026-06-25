!include "MUI2.nsh"
!include "FileFunc.nsh"

!ifndef VERSION
  !define VERSION "0.2.0"
!endif

!define APPNAME    "Battery Power Manager"
!define COMPANY    "Devon Systems"
!define APPEXE     "BatteryPowerManager.exe"
!define REGKEY     "Software\${COMPANY}\${APPNAME}"
!define UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\BatteryPowerManager"

; ── MUI Settings ─────────────────────────────────────────────────────────────
!define MUI_ABORTWARNING
!define MUI_ICON   "installer\assets\battery_power_manager.ico"
!define MUI_UNICON "installer\assets\battery_power_manager.ico"

!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_RIGHT
!define MUI_HEADERIMAGE_BITMAP    "installer\assets\header.bmp"
!define MUI_HEADERIMAGE_UNBITMAP  "installer\assets\header.bmp"

!define MUI_WELCOMEFINISHPAGE_BITMAP   "installer\assets\wizard_sidebar.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "installer\assets\wizard_sidebar.bmp"

!define MUI_WELCOMEPAGE_TITLE "Welcome to ${APPNAME} ${VERSION}"
!define MUI_WELCOMEPAGE_TEXT "This wizard will install ${APPNAME} on your computer.$\r$\n$\r$\nBattery Power Manager monitors your EcoFlow UPS and shows real-time charge, status and runtime in the system tray.$\r$\n$\r$\nClick Next to continue."

!define MUI_FINISHPAGE_TITLE "Installation Complete"
!define MUI_FINISHPAGE_TEXT "${APPNAME} has been installed successfully.$\r$\n$\r$\nThe app is now running in your system tray. Look for the battery icon near the clock."
!define MUI_FINISHPAGE_RUN "$INSTDIR\${APPEXE}"
!define MUI_FINISHPAGE_RUN_PARAMETERS "--tray"
!define MUI_FINISHPAGE_RUN_TEXT "Start Battery Power Manager"
!define MUI_FINISHPAGE_NOREBOOTSUPPORT

; ── Pages ─────────────────────────────────────────────────────────────────────
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

; ── Installer metadata ────────────────────────────────────────────────────────
Name          "${APPNAME} ${VERSION}"
OutFile       "dist\BatteryPowerManagerSetup.exe"
InstallDir    "$PROGRAMFILES64\Battery Power Manager"
InstallDirRegKey HKLM "${REGKEY}" "InstallDir"
RequestExecutionLevel admin
BrandingText  "${COMPANY}"
ShowInstDetails show

; ── Install section ───────────────────────────────────────────────────────────
Section "Battery Power Manager" SecMain
  SetRegView 64
  SetShellVarContext all

  ExecWait 'taskkill /F /IM BatteryPowerManager.exe'        $0
  ExecWait 'taskkill /F /IM BatteryPowerManagerConsole.exe' $0
  ExecWait 'taskkill /F /IM usbhid-ups.exe'                 $0
  ExecWait 'taskkill /F /IM upsd.exe'                       $0
  Sleep 1000

  RMDir /r "$INSTDIR"
  SetOutPath "$INSTDIR"
  File /r "dist\self-contained-installer\BatteryPowerManager\*"
  File /r "dist\self-contained-installer\nut"
  File "dist\self-contained-installer\battery_power_manager.ico"
  File "dist\self-contained-installer\battery_power_manager.png"
  File "installer\Start-BatteryBackend.ps1"
  File "installer\Register-BackendTask.ps1"

  WriteRegStr HKLM "${REGKEY}" "InstallDir" "$INSTDIR"
  ; Tray app starts at login (per-user GUI)
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Run" \
    "BatteryPowerManager" \
    '"$INSTDIR\BatteryPowerManager.exe" --tray'

  ; NUT backend runs as a Scheduled Task at logon (delayed 30s so it doesn't
  ; contend with WiFi / desktop init at boot), highest privileges, detached
  ; from the installer so it survives the installer closing. The register
  ; script also starts it immediately so there's no wait after install.

  WriteRegStr   HKLM "${UNINST_KEY}" "DisplayName"     "${APPNAME}"
  WriteRegStr   HKLM "${UNINST_KEY}" "DisplayVersion"  "${VERSION}"
  WriteRegStr   HKLM "${UNINST_KEY}" "Publisher"       "${COMPANY}"
  WriteRegStr   HKLM "${UNINST_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr   HKLM "${UNINST_KEY}" "DisplayIcon"     "$INSTDIR\battery_power_manager.ico"
  WriteRegStr   HKLM "${UNINST_KEY}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegDWORD HKLM "${UNINST_KEY}" "NoModify" 1
  WriteRegDWORD HKLM "${UNINST_KEY}" "NoRepair" 1
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD HKLM "${UNINST_KEY}" "EstimatedSize" "$0"

  CreateDirectory "$SMPROGRAMS\Battery Power Manager"
  CreateShortcut "$SMPROGRAMS\Battery Power Manager\Battery Power Manager.lnk" \
    "$INSTDIR\${APPEXE}" "--tray" "$INSTDIR\battery_power_manager.ico" 0
  CreateShortcut "$SMPROGRAMS\Battery Power Manager\Detail Window.lnk" \
    "$INSTDIR\${APPEXE}" "--detail-window" "$INSTDIR\battery_power_manager.ico" 0
  CreateShortcut "$SMPROGRAMS\Battery Power Manager\Test Connection.lnk" \
    "$INSTDIR\BatteryPowerManagerConsole.exe" "--once" "$INSTDIR\battery_power_manager.ico" 0
  CreateShortcut "$SMPROGRAMS\Battery Power Manager\Uninstall.lnk" \
    "$INSTDIR\Uninstall.exe" "" "$INSTDIR\battery_power_manager.ico" 0
  CreateShortcut "$DESKTOP\Battery Power Manager.lnk" \
    "$INSTDIR\${APPEXE}" "--tray" "$INSTDIR\battery_power_manager.ico" 0

  WriteUninstaller "$INSTDIR\Uninstall.exe"

  ; Register the delayed logon task and start the backend now (detached from
  ; the installer, so the NUT processes survive after this installer exits).
  nsExec::ExecToLog 'powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "$INSTDIR\Register-BackendTask.ps1"'
SectionEnd

; ── Uninstall section ─────────────────────────────────────────────────────────
Section "Uninstall"
  SetRegView 64
  SetShellVarContext all

  ExecWait 'taskkill /F /IM BatteryPowerManager.exe'        $0
  ExecWait 'taskkill /F /IM BatteryPowerManagerConsole.exe' $0
  ExecWait 'taskkill /F /IM usbhid-ups.exe'                 $0
  ExecWait 'taskkill /F /IM upsd.exe'                       $0
  Sleep 1000

  nsExec::ExecToLog 'schtasks /delete /f /tn "BatteryPowerManagerBackend"'
  DeleteRegValue HKLM "Software\Microsoft\Windows\CurrentVersion\Run" "BatteryPowerManager"
  DeleteRegKey   HKLM "${UNINST_KEY}"
  DeleteRegKey   HKLM "${REGKEY}"

  Delete "$DESKTOP\Battery Power Manager.lnk"
  Delete "$SMPROGRAMS\Battery Power Manager\Battery Power Manager.lnk"
  Delete "$SMPROGRAMS\Battery Power Manager\Detail Window.lnk"
  Delete "$SMPROGRAMS\Battery Power Manager\Test Connection.lnk"
  Delete "$SMPROGRAMS\Battery Power Manager\Uninstall.lnk"
  RMDir  "$SMPROGRAMS\Battery Power Manager"
  RMDir /r "$INSTDIR"
SectionEnd
