; libzie setup wizard (Inno Setup 6). GitHub Actions packages PyInstaller's dist\libzie folder.
; To build by hand: ISCC.exe /DAppVersion=0.1.1 installer\libzie.iss
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{EA1456F4-340D-49A5-8D02-44758B09348D}
AppName=libzie
AppVersion={#AppVersion}
AppPublisher=nopescope0
AppPublisherURL=https://github.com/nopescope0/libzie
AppSupportURL=https://github.com/nopescope0/libzie/issues
DefaultDirName={autopf}\libzie
DefaultGroupName=libzie
DisableProgramGroupPage=yes
; Installs per user without asking for administrator rights (%LOCALAPPDATA%\Programs\libzie); anyone who wants can choose "all users"
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist-installer
OutputBaseFilename=libzie-setup
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\libzie.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"; InfoBeforeFile: "privacy-en.txt"
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"; InfoBeforeFile: "privacy-tr.txt"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\libzie\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{autoprograms}\libzie"; Filename: "{app}\libzie.exe"
Name: "{autodesktop}\libzie"; Filename: "{app}\libzie.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\libzie.exe"; Description: "{cm:LaunchProgram,libzie}"; Flags: nowait postinstall skipifsilent
; The in-app update runs the wizard silently; libzie is reopened when it finishes
Filename: "{app}\libzie.exe"; Flags: nowait runasoriginaluser; Check: WizardSilent
