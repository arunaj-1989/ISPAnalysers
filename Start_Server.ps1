<#
.SYNOPSIS
    Sets up the environment and runs the Flask-based ISP Analyser application.
.DESCRIPTION
    This script automates the setup and execution of the entire application. It performs the following steps:
    1. Validates that Python 3.11 or newer is installed.
    2. Checks for and helps install necessary build tools (MSVC, Rust).
    3. Installs Ollama and pulls the required model if not present.
    4. Creates a Python virtual environment if it doesn't exist.
    5. Installs required packages from 'requirements.txt'.
    6. Verifies GPU support for PyTorch.
    7. Launches the Flask web application.
.NOTES
    - Must be run from the root directory of the project.
    - Requires PowerShell 5.1 or later.
    - To stop the server, press CTRL+C in the PowerShell window.
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
$FlaskScript = Join-Path $ScriptDir "app.py"
$OllamaModel = "llama3" # Match the model used in the API

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

# --- 1b. Check for NVIDIA CUDA ---
Write-Log "Step 1b: Checking for NVIDIA CUDA..."
$cudaPath = $env:CUDA_PATH
if (-not ($cudaPath -and (Test-Path $cudaPath))) {
    Write-Log "Warning: CUDA_PATH environment variable not found or path is invalid." -Color Yellow
    Write-Log "GPU acceleration for PyTorch may fail. Ensure the NVIDIA CUDA Toolkit is installed and CUDA_PATH is set." -Color Yellow
}

# --- 1c. Check for C++ Build Tools (required for Rust on Windows) ---
Write-Log "Step 1c: Checking for MSVC C++ Build Tools..."
$vswherePath = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
if (Test-Path $vswherePath) {
    $vcToolsPath = & $vswherePath -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    if ($vcToolsPath) {
        Write-Log "Found C++ Build Tools at '$vcToolsPath'." -Color Green
    } else {
        Write-Log "Error: The required 'Desktop development with C++' workload was not found." -Color Red
        Write-Log "Please install it via the Visual Studio Installer." -Color Red
        Write-Log "You can download the installer from: https://visualstudio.microsoft.com/visual-cpp-build-tools/" -Color Red
        exit 1
    }
} else {
    Write-Log "Error: Visual Studio Installer (and vswhere.exe) not found." -Color Red
    Write-Log "The C++ Build Tools are required to compile some dependencies." -Color Red
    Write-Log "Please install the 'Desktop development with C++' workload from:" -Color Red
    Write-Log "https://visualstudio.microsoft.com/visual-cpp-build-tools/" -Color Red
    exit 1
}

# --- 1d. Check for Rust/Cargo ---
Write-Log "Step 1d: Checking for Rust (required for some dependencies)..."
$cargoExe = Get-Command -Name "cargo" -ErrorAction SilentlyContinue
if (-not $cargoExe) {
    Write-Log "Warning: Rust's build tool 'cargo' was not found in your PATH." -Color Yellow
    Write-Log "Some Python packages (like 'cryptography') need Rust to compile." -Color Yellow
    $choice = Read-Host "Do you want to attempt to install Rust now via rustup.rs? (y/n)"
    if ($choice -eq 'y') {
        Write-Log "Installing Rust via rustup..."
        # Download and execute the rustup-init installer
        $rustupInstaller = "$env:TEMP\rustup-init.exe"
        Invoke-WebRequest https://win.rustup.rs/x86_64 -OutFile $rustupInstaller
        & $rustupInstaller -y # Install with defaults, non-interactively. This will modify the PATH.
        Remove-Item $rustupInstaller
        Write-Log "Rust has been installed. Please RESTART your terminal and run this script again to ensure 'cargo' is in the PATH." -Color Green
        exit 0 # Exit gracefully to allow user to restart terminal
    } else {
        Write-Log "Please install Rust from https://rustup.rs/ and restart your terminal before running this script again." -Color Red
        exit 1
    }
}

# --- 1e. Install Ollama ---
Write-Log "Step 1e: Checking for Ollama..."
$ollamaExe = Get-Command -Name "ollama" -ErrorAction SilentlyContinue
if (-not $ollamaExe) {
    Write-Log "Ollama not found. Attempting to install..." -Color Yellow
    try {
        Invoke-Expression (Invoke-WebRequest -Uri https://ollama.com/install.ps1 -UseBasicParsing).Content
        Write-Log "Ollama installed successfully." -Color Green
    } catch {
        Write-Log "Failed to install Ollama. Please install it manually from https://ollama.com" -Color Red
        exit 1
    }
}
Write-Log "Ensuring Ollama model '$OllamaModel' is available..."
ollama pull $OllamaModel

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

# --- 3b. Verify PyTorch CUDA Availability ---
Write-Log "Step 3b: Verifying PyTorch can access the GPU..."
try {
    $cudaCheckResult = & $PythonVenvExe -c "import torch; print(torch.cuda.is_available())"
    if ($cudaCheckResult -eq "True") {
        Write-Log "PyTorch successfully detected the NVIDIA GPU." -Color Green
    }
    else {
        Write-Log "Warning: PyTorch is installed but cannot detect a compatible NVIDIA GPU. The app will run on the CPU." -Color Yellow
    }
} catch {
    Write-Log "Failed to run PyTorch CUDA check. There might be an issue with the installation." -Color Red
}

# --- 4. Run the Application ---
Write-Log "Step 4: Launching the Flask application..."

if (-not (Test-Path -Path $FlaskScript)) {
    Write-Log "Flask application script '$FlaskScript' not found!" -Color Red
    exit 1
}

Write-Log "You can access the app at http://127.0.0.1:5000. Press CTRL+C in this window to stop the server." -Color Cyan
& $PythonVenvExe $FlaskScript