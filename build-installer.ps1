param(
    [string]$Python = "$PSScriptRoot\.venv\Scripts\python.exe",
    [string]$Compiler = 'ISCC.exe',
    [string]$OutputDirectory = "$PSScriptRoot\dist\installer",
    [string]$CertificateThumbprint = '',
    [string]$SignTool = 'signtool.exe',
    [string]$TimestampUrl = 'http://timestamp.digicert.com'
)
$ErrorActionPreference = 'Stop'
$taskBuildRoot = Join-Path $PSScriptRoot 'build\installer'
$taskDistRoot = Join-Path $taskBuildRoot 'dist'
New-Item -ItemType Directory -Path $taskBuildRoot, $OutputDirectory -Force | Out-Null
& $Python -m PyInstaller --noconfirm --clean --noupx --windowed --onedir --name AionPulse --version-file "$PSScriptRoot\installer\version-info.txt" --icon "$PSScriptRoot\assets\aionpulse.ico" --add-data "$PSScriptRoot\assets;assets" --add-data "$PSScriptRoot\LICENSE;licenses" --distpath $taskDistRoot --workpath "$taskBuildRoot\work" --specpath $taskBuildRoot "$PSScriptRoot\desktop.py"
if ($LASTEXITCODE -ne 0) { throw 'Falha ao empacotar o aplicativo.' }
$taskBundle = Join-Path $taskDistRoot 'AionPulse'
function Sign-ReleaseFile([string]$FilePath) {
    & $SignTool sign /sha1 $CertificateThumbprint /fd SHA256 /tr $TimestampUrl /td SHA256 $FilePath
    if ($LASTEXITCODE -ne 0) { throw "Falha ao assinar $FilePath" }
    & $SignTool verify /pa $FilePath
    if ($LASTEXITCODE -ne 0) { throw "Assinatura não confiável: $FilePath" }
}
if ($CertificateThumbprint) { Sign-ReleaseFile "$taskBundle\AionPulse.exe" }
$taskLicenses = Join-Path $taskBundle '_internal\licenses'
& $Python "$PSScriptRoot\collect-licenses.py" $taskLicenses
if ($LASTEXITCODE -ne 0) { throw 'Falha ao reunir licenças.' }
Copy-Item -LiteralPath "$PSScriptRoot\README.md", "$PSScriptRoot\THIRD_PARTY.md" -Destination $taskBundle
Copy-Item -LiteralPath "$PSScriptRoot\docs" -Destination $taskBundle -Recurse -Force
& $Python "$PSScriptRoot\export-source.py" "$taskBundle\source\AionPulse-source.zip"
if ($LASTEXITCODE -ne 0) { throw 'Falha ao incluir o código-fonte.' }
& $Compiler /Q "/DBundleDirectory=$taskBundle" "/DOutputDirectory=$OutputDirectory" "$PSScriptRoot\installer\AionPulse.iss"
if ($LASTEXITCODE -ne 0) { throw 'Falha ao compilar o instalador.' }
$taskInstaller = Join-Path $OutputDirectory 'AionPulse-Setup-0.1.0-beta.1-x64.exe'
if ($CertificateThumbprint) { Sign-ReleaseFile $taskInstaller }
Get-FileHash -LiteralPath $taskInstaller -Algorithm SHA256 | Format-List
