; ============================================================
;  Synapso — Inno Setup Installer Script
;  Requires Inno Setup 6.x (https://jrsoftware.org/isinfo.php)
;
;  Build command (from any Inno Setup-capable machine):
;    iscc installer\synapso_setup.iss
;  Or open in the Inno Setup Compiler GUI and press F9.
;
;  Output: installer\Output\Synapso_Setup_v1.0.0.exe
; ============================================================

#define AppName        "Synapso"
#define AppVersion     "1.0.0"
#define AppPublisher   "Synapso"
#define AppExeName     "Synapso.exe"
#define AppIcon        "..\resources\images\graphics\synapso.ico"
#define SourceDir      "..\dist\Synapso"

[Setup]
AppId                     = {{A3F7C2D1-84BE-4E5A-9B3C-D0F16E28A741}
AppName                   = {#AppName}
AppVersion                = {#AppVersion}
AppPublisherURL           = https://synapso.world
AppSupportURL             = https://github.com/wrex1k/Synapso
AppUpdatesURL             = https://github.com/wrex1k/Synapso
AppPublisher              = {#AppPublisher}
AppCopyright              = Copyright (C) 2026 {#AppPublisher}

DefaultDirName            = {autopf}\{#AppName}
DefaultGroupName          = {#AppName}
DisableProgramGroupPage   = yes

OutputDir                 = Output
OutputBaseFilename        = Synapso_Setup
SetupIconFile             = {#AppIcon}

Compression               = lzma2/ultra64
SolidCompression          = yes
LZMAUseSeparateProcess    = yes

WizardStyle               = modern
WizardResizable           = no

ArchitecturesAllowed            = x64compatible
ArchitecturesInstallIn64BitMode = x64compatible

PrivilegesRequired        = admin
PrivilegesRequiredOverridesAllowed = dialog

UninstallDisplayIcon      = {app}\{#AppExeName}
UninstallDisplayName      = {#AppName} {#AppVersion}

MinVersion                = 10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

; ── Files ───────────────────────────────────────────────────────────────────
[Files]
; Recursively copy everything PyInstaller placed in dist\Synapso\
Source: "{#SourceDir}\*"; \
    DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

; ── Shortcuts ───────────────────────────────────────────────────────────────
[Icons]
; Start Menu entry
Name: "{group}\{#AppName}";         \
    Filename: "{app}\{#AppExeName}"; \
    IconFilename: "{app}\{#AppExeName}"; \
    WorkingDir: "{app}"

; Start Menu — Uninstall entry
Name: "{group}\Uninstall {#AppName}"; \
    Filename: "{uninstallexe}"

; Desktop shortcut (created for all users because we run as admin)
Name: "{commondesktop}\{#AppName}"; \
    Filename: "{app}\{#AppExeName}"; \
    IconFilename: "{app}\{#AppExeName}"; \
    WorkingDir: "{app}"; \
    Tasks: desktopicon

; ── Tasks (optional components the user can toggle) ─────────────────────────
[Tasks]
Name: "desktopicon"; \
    Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; \
    Flags: unchecked

; ── Run after install ───────────────────────────────────────────────────────
[Run]
Filename: "{app}\{#AppExeName}"; \
    Description: "{cm:LaunchProgram,{#StringChange(AppName, '&', '&&')}}"; \
    Flags: nowait postinstall skipifsilent

; ── Registry — optional: associate a file extension or store install path ───
; Uncomment the block below if you want to record the install location
; in the registry (useful for update scripts that need to find the install dir).
;[Registry]
;Root: HKLM; Subkey: "Software\{#AppPublisher}\{#AppName}"; \
;    ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"; \
;    Flags: createvalueifdoesnt

; ── Custom uninstall cleanup ────────────────────────────────────────────────
; Removes the installation directory only if it is empty after uninstall
; (files created at runtime, e.g. logs or .env, are left to the user).
[UninstallDelete]
Type: dirifempty; Name: "{app}"
