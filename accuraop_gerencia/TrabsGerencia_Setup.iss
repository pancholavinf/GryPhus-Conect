; Script de Inno Setup para Trabs Gerencia
; Requiere Inno Setup 6 (https://jrsoftware.org/isdl.php)

#define MyAppName "Trabs Gerencia"
#define MyAppVersion "1.0.6"
#define MyAppPublisher "Accuratek - Trabs - Francisco lavin"
#define MyAppURL "https://accuratek.cl"
#define MyAppExeName "TrabsGerencia.exe"

[Setup]
; Identificador único de la aplicación (GUID generado para Trabs Gerencia)
AppId={{D3F9B7C1-28EA-4E5B-9A71-55823190B1E2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\TrabsGerencia
DisableProgramGroupPage=yes
; Icono del instalador
SetupIconFile=assets\app_icon.ico
OutputDir=dist_installer
OutputBaseFilename=TrabsGerencia_Setup_v{#MyAppVersion}
; Máxima compresión con LZMA2 Ultra Solid
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
LZMADictionarySize=262144
LZMANumBlockThreads=1
WizardStyle=modern
PrivilegesRequired=lowest
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Copiar todo el directorio de distribución generado por PyInstaller
Source: "dist\TrabsGerencia\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\_internal\assets\app_icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; IconFilename: "{app}\_internal\assets\app_icon.ico"

[Run]
Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Filename: "{app}\{#MyAppExeName}"; Flags: nowait postinstall skipifsilent
