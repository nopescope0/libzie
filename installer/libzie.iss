; libzie kurulum sihirbazı (Inno Setup 6). GitHub Actions, PyInstaller'ın dist\libzie klasörünü paketler.
; Elle derlemek için: ISCC.exe /DAppVersion=0.1.1 installer\libzie.iss
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
; Yönetici izni istemeden kullanıcıya özel kurulur (%LOCALAPPDATA%\Programs\libzie); isteyen "tüm kullanıcılar"ı seçebilir
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist-installer
OutputBaseFilename=libzie-kurulum
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\libzie.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "Masaüstüne kısayol oluştur"; GroupDescription: "Ek görevler:"; Flags: unchecked

[Files]
Source: "..\dist\libzie\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{autoprograms}\libzie"; Filename: "{app}\libzie.exe"
Name: "{autodesktop}\libzie"; Filename: "{app}\libzie.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\libzie.exe"; Description: "libzie'yi başlat"; Flags: nowait postinstall skipifsilent
; Uygulama içi güncelleme sihirbazı sessiz çalıştırır; bitince libzie yeniden açılır
Filename: "{app}\libzie.exe"; Flags: nowait runasoriginaluser; Check: WizardSilent
