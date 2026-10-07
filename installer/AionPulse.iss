#ifndef BundleDirectory
  #error BundleDirectory is required
#endif
#ifndef OutputDirectory
  #define OutputDirectory "..\dist\installer"
#endif

[Setup]
AppId={{0EF12FA7-C73A-450C-9801-A8C2C30E0655}
AppName=AionPulse
AppVersion=0.1.0 Beta 1
AppVerName=AionPulse 0.1.0 Beta 1
AppPublisher=GabrielMartorello
AppPublisherURL=https://github.com/GabrielMartorello
DefaultDirName={localappdata}\Programs\AionPulse
DefaultGroupName=AionPulse
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
MinVersion=10.0
OutputDir={#OutputDirectory}
OutputBaseFilename=AionPulse-Setup-0.1.0-beta.1-x64
SetupIconFile=..\assets\aionpulse.ico
UninstallDisplayIcon={app}\AionPulse.exe
LicenseFile=..\LICENSE
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
Uninstallable=yes

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
brazilianportuguese.DesktopIcon=Criar atalho na área de trabalho
english.DesktopIcon=Create a desktop shortcut
brazilianportuguese.NpcapTask=Baixar e instalar o Npcap pelo site oficial (necessário para capturar o jogo)
english.NpcapTask=Download and install Npcap from its official website (required for game capture)
brazilianportuguese.DependencyTitle=Dependência de captura
english.DependencyTitle=Capture dependency
brazilianportuguese.DependencyInfo=Python e bibliotecas já estão incluídos. O Npcap será baixado do site oficial; conclua o assistente dele e aceite a solicitação de administrador do Windows.
english.DependencyInfo=Python and libraries are included. Npcap will be downloaded from its official website; complete its wizard and accept the Windows administrator prompt.
brazilianportuguese.NpcapFailed=O Npcap não foi instalado. Conclua o assistente ou desmarque essa opção para instalar o AionPulse sem captura. Download oficial: https://npcap.com/#download
english.NpcapFailed=Npcap was not installed. Complete its wizard or uncheck this option to install AionPulse without capture. Official download: https://npcap.com/#download
brazilianportuguese.SilentNpcap=Instale o Npcap pelo site oficial antes de executar uma instalação silenciosa, ou desmarque a tarefa npcap.
english.SilentNpcap=Install Npcap from its official website before running a silent installation, or deselect the npcap task.
brazilianportuguese.Launch=Iniciar AionPulse
english.Launch=Launch AionPulse

[Tasks]
Name: "desktopicon"; Description: "{cm:DesktopIcon}"
Name: "npcap"; Description: "{cm:NpcapTask}"; Check: NeedsNpcap

[Files]
Source: "{#BundleDirectory}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\AionPulse"; Filename: "{app}\AionPulse.exe"; Parameters: "--show-main"; WorkingDir: "{app}"
Name: "{autodesktop}\AionPulse"; Filename: "{app}\AionPulse.exe"; Parameters: "--show-main"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\AionPulse.exe"; Parameters: "--show-main"; Description: "{cm:Launch}"; Flags: nowait postinstall skipifsilent

[Code]
var
  DownloadPage: TDownloadWizardPage;
  DriverRestart: Boolean;

function NeedsNpcap: Boolean;
begin
  Result := not FileExists(ExpandConstant('{sys}\Npcap\wpcap.dll'));
end;

procedure InitializeWizard;
begin
  DownloadPage := CreateDownloadPage(CustomMessage('DependencyTitle'), CustomMessage('DependencyInfo'), nil);
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ExitCode: Integer;
begin
  Result := '';
  if not NeedsNpcap or not WizardIsTaskSelected('npcap') then Exit;
  if WizardSilent then begin
    Result := CustomMessage('SilentNpcap');
    Exit;
  end;
  DownloadPage.Clear;
  DownloadPage.Add('https://npcap.com/dist/npcap-1.89.exe', 'npcap-1.89.exe', '8aed85e900d783d1308506e919587d3e540451947af8a82f2d04f819e44305cc');
  DownloadPage.Show;
  try
    try
      DownloadPage.Download;
      if not ShellExec('runas', ExpandConstant('{tmp}\npcap-1.89.exe'), '', '', SW_SHOWNORMAL, ewWaitUntilTerminated, ExitCode) then
        Result := CustomMessage('NpcapFailed')
      else if NeedsNpcap then
        Result := CustomMessage('NpcapFailed')
      else if ExitCode = 3010 then begin
        DriverRestart := True;
        NeedsRestart := True;
      end;
    except
      Result := GetExceptionMessage;
    end;
  finally
    DownloadPage.Hide;
  end;
end;

function NeedRestart: Boolean;
begin
  Result := DriverRestart;
end;
