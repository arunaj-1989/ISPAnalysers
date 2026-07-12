<#
.SYNOPSIS
    Sets up the environment and runs the ISP Analysers Streamlit application.
.DESCRIPTION
    This script automates the setup and execution of the application. It performs the following steps:
    1. Validates that Python 3.11 or newer is installed.
    2. Installs Ollama and pulls the required model if not present.
    3. Creates a Python virtual environment if it doesn't exist.
    4. Installs required packages from 'requirements.txt' and verifies GPU support.
    5. Pre-caches Whisper and OCR models to avoid download on first use.
    6. Launches the Streamlit application, making it available on the network.
.NOTES
    - Assumes a 'requirements.txt' file exists in the same directory.
    - Must be run from the root directory of the project.
    - Requires PowerShell 5.1 or later.
#>

[CmdletBinding()]
param ()

$ErrorActionPreference = 'Stop'
$ScriptDir = $PSScriptRoot

# --- Configuration ---
$PythonVersionMajor = 3
$PythonVersionMinor = 11
$VenvDir = Join-Path $ScriptDir ".venv"
$RequirementsFile = Join-Path $ScriptDir "requirements.txt"
$WhisperCacheScript = Join-Path $ScriptDir "pre_cache_models.py"
$OcrCacheScript = Join-Path $ScriptDir "pre_cache_ocr_models.py"
$StreamlitApp = Join-Path $ScriptDir "Home.py"

# --- Helper Functions ---
function Write-Log {
    param([string]$Message, [string]$Color = "White")
    Write-Host "[$([DateTime]::Now.ToString('HH:mm:ss'))] " -NoNewline
    Write-Host $Message -ForegroundColor $Color
}

# --- 1. Check for Python ---
Write-Log "Step 1: Checking for Python ${PythonVersionMajor}.${PythonVersionMinor}+..."
$pythonExe = Get-Command -Name "python" -ErrorAction SilentlyContinue
if (-not $pythonExe) {
    Write-Log "Python not found in PATH. Please install Python ${PythonVersionMajor}.${PythonVersionMinor} or higher and ensure it's in your PATH." -Color Red
    exit 1
}

$versionString = (& $pythonExe.Source --version)
if ($versionString -match "(\d+)\.(\d+)") {
    $major = [int]$matches[1]
    $minor = [int]$matches[2]
    if ($major -lt $PythonVersionMajor -or ($major -eq $PythonVersionMajor -and $minor -lt $PythonVersionMinor)) {
        Write-Log "Found Python version ${major}.${minor}. Version ${PythonVersionMajor}.${PythonVersionMinor} or higher is required." -Color Red
        exit 1
    }
    Write-Log "Found compatible Python version at $($pythonExe.Source)" -Color Green
}
else {
    Write-Log "Could not determine Python version from string: $versionString" -Color Red
    exit 1
}

# Check for CUDA
Write-Log "Step 1b: Checking for NVIDIA CUDA..."
$cudaPath = $env:CUDA_PATH
if (-not ($cudaPath -and (Test-Path $cudaPath))) {
    Write-Log "Warning: CUDA_PATH environment variable not found or path is invalid." -Color Yellow
    Write-Log "GPU acceleration for PyTorch may fail. Ensure the NVIDIA CUDA Toolkit is installed and CUDA_PATH is set." -Color Yellow
    Write-Log "(Example: C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v12.1)" -Color Yellow
}

# --- 1c. Install Ollama ---
Write-Log "Step 1c: Checking for Ollama..."
$ollamaExe = Get-Command -Name "ollama" -ErrorAction SilentlyContinue
if (-not $ollamaExe) {
    Write-Log "Ollama not found. Installing Ollama..." -Color Yellow
    try {
        Invoke-Expression (Invoke-WebRequest -Uri https://ollama.com/install.ps1 -UseBasicParsing).Content
        Write-Log "Ollama installed successfully. The service will start on boot." -Color Green
    } catch {
        Write-Log "Failed to install Ollama. Please install it manually from https://ollama.com" -Color Red
        exit 1
    }
}
Write-Log "Ensuring Ollama model 'phi3' is available..."
# This command is idempotent; it will only download if the model is missing.
ollama pull phi3

# --- 2. Setup Virtual Environment ---
Write-Log "Step 2: Checking for virtual environment..."
if (-not (Test-Path -Path $VenvDir)) {
    Write-Log "Virtual environment not found. Creating one at '$VenvDir'..." -Color Yellow
    & $pythonExe.Source -m venv $VenvDir
    Write-Log "Virtual environment created." -Color Green
}
else {
    Write-Log "Virtual environment already exists." -Color Green
}

# Define paths to executables inside the venv
$PipExe = Join-Path -Path $VenvDir -ChildPath "Scripts\pip.exe"
$PythonVenvExe = Join-Path -Path $VenvDir -ChildPath "Scripts\python.exe"
$StreamlitExe = Join-Path -Path $VenvDir -ChildPath "Scripts\streamlit.exe"

# --- 3. Install Dependencies ---
Write-Log "Step 3: Installing dependencies from '$RequirementsFile'..."
if (-not (Test-Path -Path $RequirementsFile)) {
    Write-Log "'$RequirementsFile' not found. Cannot install dependencies." -Color Red
    exit 1
}
try {
    & $PipExe install --upgrade pip
    & $PipExe install -r $RequirementsFile
    Write-Log "Dependencies installed successfully." -Color Green
}
catch {
    Write-Log "Failed to install dependencies. Please check your network connection and '$RequirementsFile'." -Color Red
    Write-Log $_.Exception.Message -Color Red
    exit 1
}

# --- 3b. Check PyTorch CUDA Availability ---
Write-Log "Step 3b: Verifying PyTorch can access the GPU..."
try {
    $cudaCheckResult = & $PythonVenvExe -c "import torch; print(torch.cuda.is_available())"
    if ($cudaCheckResult -eq "True") {
        Write-Log "PyTorch successfully detected the NVIDIA GPU." -Color Green
    }
    else {
        Write-Log "Error: PyTorch is installed but cannot detect a compatible NVIDIA GPU." -Color Red
        Write-Log "Please check the following:" -Color Yellow
        Write-Log "1. Your NVIDIA drivers are up to date." -Color Yellow
        Write-Log "2. You have the CUDA Toolkit v12.1 installed." -Color Yellow
        Write-Log "3. The CUDA_PATH environment variable is set correctly." -Color Yellow
        exit 1
    }
} catch {
    Write-Log "Failed to run PyTorch CUDA check. There might be an issue with the installation." -Color Red
}

# --- 4. Pre-cache Models ---
Write-Log "Step 4: Pre-caching machine learning models..."
try {
    Write-Log "Caching Whisper models..."
    & $PythonVenvExe $WhisperCacheScript
    Write-Log "Caching EasyOCR models..."
    & $PythonVenvExe $OcrCacheScript
    Write-Log "Model caching complete." -Color Green
}
catch {
    Write-Log "An error occurred during model caching. The application will attempt to download them on first use." -Color Yellow
    Write-Log $_.Exception.Message -Color Yellow
}

# --- 5. Run the Application ---
Write-Log "Step 5: Launching the Streamlit application..."

# This prevents a common "WinError 1114" crash on Windows systems with Anaconda/MKL installed,
# which can cause conflicts with PyTorch's OpenMP libraries.
Write-Log "Setting KMP_DUPLICATE_LIB_OK to TRUE to prevent potential DLL conflicts."
$env:KMP_DUPLICATE_LIB_OK = "TRUE"

Write-Log "You can access the app in your browser. Press CTRL+C in this window to stop the server."

& $StreamlitExe run $StreamlitApp --server.address=0.0.0.0 --server.port=8501