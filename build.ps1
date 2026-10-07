$ErrorActionPreference = 'Stop'
$compiler = Join-Path $env:WINDIR 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
if (-not (Test-Path -LiteralPath $compiler)) {
    throw 'Instale o .NET Framework 4.x para compilar o iniciador.'
}
& $compiler /nologo /target:winexe /optimize+ "/win32icon:$PSScriptRoot\assets\aionpulse.ico" "/out:$PSScriptRoot\AionPulse.exe" /reference:System.Windows.Forms.dll "$PSScriptRoot\AionPulseLauncher.cs"
if ($LASTEXITCODE -ne 0) { throw 'Falha ao compilar AionPulse.exe.' }
Write-Output 'AionPulse.exe criado.'
