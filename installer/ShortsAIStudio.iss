#define MyAppName "Shorts AI Studio"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Shorts AI Studio"
#define MyAppExeName "ShortsAIStudio.exe"

[Setup]
AppId={{D91B74A3-6B83-4E58-AE21-7A82B1BEE521}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Shorts AI Studio
DefaultGroupName={#MyAppName}
OutputDir=..\Output
OutputBaseFilename=Shorts_AI_Studio_Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
UninstallDisplayIcon={app}\{#MyAppExeName}

[Files]
Source: "..\dist\ShortsAIStudio\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные задачи:";

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Запустить Shorts AI Studio"; Flags: nowait postinstall skipifsilent
