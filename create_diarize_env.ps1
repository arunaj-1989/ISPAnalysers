param(
    [Parameter()]
    [ValidateSet('windows','ubuntu')]
    [string]$Target = 'windows'
)

$ErrorActionPreference = 'Stop'
$ScriptDir = $PSScriptRoot
$VenvName = ".venv-diarize-$Target"
$VenvPath = Join-Path $ScriptDir $VenvName

Write-Host "Creating diarization environment for: $Target" -ForegroundColor Cyan

if (-not (Test-Path $VenvPath)) {
    if ($Target -eq 'windows') {
        py -3.10 -m venv $VenvPath
    } else {
        python3.10 -m venv $VenvPath
    }
} else {
    Write-Host "Virtual environment already exists: $VenvPath" -ForegroundColor Yellow
}

$PythonExe = Join-Path $VenvPath "Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    $PythonExe = Join-Path $VenvPath "bin/python"
}

Write-Host "Upgrading pip..." -ForegroundColor Cyan
& $PythonExe -m pip install --upgrade pip setuptools wheel

if ($Target -eq 'windows') {
    Write-Host "Installing Windows diarization stack..." -ForegroundColor Cyan
    & $PythonExe -m pip install "numpy<2" torch==2.1.2 torchvision==0.16.2 torchaudio==2.1.2
    & $PythonExe -m pip install -r (Join-Path $ScriptDir 'requirements-diarize-win.txt')
} else {
    Write-Host "Installing Ubuntu diarization stack..." -ForegroundColor Cyan
    & $PythonExe -m pip install "numpy<2" torch==2.1.2+cu121 torchvision==0.16.2+cu121 torchaudio==2.1.2+cu121 -f https://download.pytorch.org/whl/cu121
    & $PythonExe -m pip install -r (Join-Path $ScriptDir 'requirements-diarize-ubuntu.txt')
}

Write-Host "Environment ready. Activate with:" -ForegroundColor Green
if ($Target -eq 'windows') {
    Write-Host "  .\$VenvName\Scripts\Activate.ps1" -ForegroundColor White
} else {
    Write-Host "  source $VenvName/bin/activate" -ForegroundColor White
}
