; Script de Inno Setup para GryPhus Conect Gerencia
; Requiere Inno Setup 6 (https://jrsoftware.org/isdl.php)

#define MyAppName "GryPhus Conect Gerencia"
#define MyAppVersion "1.1.8"
#define MyAppPublisher "Gryphus Systems - Francisco Lavin"
#define MyAppURL "https://github.com/pancholavinf/GryPhus-Conect"
#define MyAppExeName "GryPhusConectGerencia.exe"

[Setup]
; Identificador único de la aplicación (Mantiene el mismo AppId para actualizar sobre instalaciones existentes)
AppId={{D3F9B7C1-28EA-4E5B-9A71-55823190B1E2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\GryPhusConectGerencia
DisableProgramGroupPage=yes
; Icono del instalador y del desinstalador
SetupIconFile=assets\gryphus_conect_icon.ico
UninstallDisplayIcon={app}\gryphus_conect_icon.ico
UsePreviousTasks=no
OutputDir=dist_installer
OutputBaseFilename=GryPhusConectGerencia_Setup_v{#MyAppVersion}
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
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[InstallDelete]
; Limpiar accesos directos anteriores para forzar recarga limpia del icono en Windows
Type: files; Name: "{autoprograms}\Trabs Gerencia.lnk"
Type: files; Name: "{autodesktop}\Trabs Gerencia.lnk"
Type: files; Name: "{autoprograms}\{#MyAppName}.lnk"
Type: files; Name: "{autodesktop}\{#MyAppName}.lnk"
Type: files; Name: "{app}\TrabsGerencia.exe"

[Files]
; Copiar todo el directorio de distribución generado por PyInstaller
Source: "dist\GryPhusConectGerencia\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "assets\gryphus_conect_icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\gryphus_conect_icon.ico"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\gryphus_conect_icon.ico"

[Run]
Filename: "{sys}\ie4uinit.exe"; Parameters: "-show"; Flags: runhidden nowait skipifdoesntexist
Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Filename: "{app}\{#MyAppExeName}"; Flags: nowait postinstall skipifsilent

[Code]
procedure SHChangeNotify(wEventId: Integer; uFlags: Cardinal; dwItem1: Integer; dwItem2: Integer);
  external 'SHChangeNotify@shell32.dll stdcall';

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    SHChangeNotify($08000000, $0000, 0, 0);
  end;
end;
