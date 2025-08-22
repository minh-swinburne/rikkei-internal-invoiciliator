
; Invoice Reconciliator NSIS Installer Script
; Generated automatically by build script

!define APP_NAME "Invoice Reconciliator"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "KDDI"
!define APP_DESCRIPTION "Automated Invoice/PO Reconciliation Tool"
!define APP_WEBSITE "https://github.com/minh-swinburne/rikkei-internal-invoiciliator"

; Main application file
!define MAIN_APP_EXE "InvoiceReconciliator.exe"

; Use Modern UI
!include "MUI2.nsh"

; General configuration
Name "${APP_NAME}"
OutFile "InvoiceReconciliator-v1.0.0-Setup.exe"
InstallDir "$PROGRAMFILES\${APP_NAME}"
InstallDirRegKey HKCU "Software\${APP_NAME}" ""
RequestExecutionLevel admin

; Interface settings
!define MUI_ABORTWARNING
!define MUI_ICON "src\assets\icon.ico"
!define MUI_UNICON "src\assets\icon.ico"

; Pages
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Languages
!insertmacro MUI_LANGUAGE "English"

; Version information
VIProductVersion "1.0.0.0.0.0"
VIAddVersionKey "ProductName" "${APP_NAME}"
VIAddVersionKey "CompanyName" "${APP_PUBLISHER}"
VIAddVersionKey "FileDescription" "${APP_DESCRIPTION}"
VIAddVersionKey "FileVersion" "1.0.0"

; Installation section
Section "Main Application" SecMain
    SetOutPath "$INSTDIR"
    
    ; Add files
    File "dist\InvoiceReconciliator.exe"
    File ".env.template"
    File "src\assets\USER_GUIDE.md"
    
    ; Create shortcuts
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${MAIN_APP_EXE}"
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${MAIN_APP_EXE}"
    
    ; Registry entries
    WriteRegStr HKCU "Software\${APP_NAME}" "" $INSTDIR
    
    ; Uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\Uninstall.exe"
SectionEnd

; Uninstaller section
Section "Uninstall"
    Delete "$INSTDIR\InvoiceReconciliator.exe"
    Delete "$INSTDIR\.env.template"
    Delete "$INSTDIR\USER_GUIDE.md"
    Delete "$INSTDIR\Uninstall.exe"
    
    RMDir "$INSTDIR"
    
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    RMDir "$SMPROGRAMS\${APP_NAME}"
    Delete "$DESKTOP\${APP_NAME}.lnk"
    
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
    DeleteRegKey HKCU "Software\${APP_NAME}"
SectionEnd
