#define MyAppName "Строймаркет Цаков BGN-EUR Конвертор"
#define MyAppVersion "2.0.1"
#define MyAppPublisher "Здравко Павлов \ BunchVFX"
#define MyAppURL ""
#define MyAppExeName "BGN_EUR_Converter.exe"

[Setup]
AppId={{3BBE9AF2-2CD3-4A6D-840C-FBB3D3E0C350}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={commonpf32}\Строймаркет_Цаков\BGN_EUR_Converter
DefaultGroupName={#MyAppName}
SetupIconFile=D:\PERSONAL\STROIMARKET\TOOLS\Currency Coverter\icon.ico
UninstallDisplayIcon=D:\PERSONAL\STROIMARKET\TOOLS\Currency Coverter\icon.ico
OutputDir=./installer
OutputBaseFilename=BGN-EUR_Converter_Installer
Compression=lzma
SolidCompression=yes
CreateAppDir=yes
Uninstallable=yes
; Remove the signing line unless you buy a cert
; SignTool=

[Languages]
Name: "bulgarian"; MessagesFile: "compiler:Languages\Bulgarian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Създай пряк път на работния плот"; GroupDescription: "Options:"
Name: "runonstartup"; Description: "Стартирай автоматично с Windows"; GroupDescription: "Options:"

[Files]
Source: "D:\PERSONAL\STROIMARKET\TOOLS\Currency Coverter\dist\BGN_EUR_Converter\BGN_EUR_Converter.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "D:\PERSONAL\STROIMARKET\TOOLS\Currency Coverter\icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "D:\PERSONAL\STROIMARKET\TOOLS\Currency Coverter\dist\BGN_EUR_Converter\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
; Optional: add settings.json if you want user settings to persist through uninstall/reinstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"
Name: "{userdesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\icon.ico"; Tasks: runonstartup

[InstallDelete]
Type: filesandordirs; Name: "{app}"
