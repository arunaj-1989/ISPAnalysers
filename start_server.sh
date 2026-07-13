#!/bin/bash
#
# SYNOPSIS
#   Sets up the environment and runs the Flask-based ISP Analyser application.
#
# DESCRIPTION
#   This script automates the setup and execution of the entire application. It performs the following steps:
#   1. Validates that Python 3.11 or newer is installed.
#   2. Checks for and helps install Rust.
#   3. Installs Ollama and pulls the required model if not present.
#   4. Creates a Python virtual environment if it doesn't exist.
#   5. Installs required packages from 'requirements.txt'.
#   6. Verifies GPU support for PyTorch.
#   7. Launches the Flask web application.
#
# NOTES
#   - Must be run from the root directory of the project.
#   - To stop the server, press CTRL+C in the terminal window.

set -e # Exit immediately if a command exits with a non-zero status.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# --- Configuration ---
PYTHON_VERSION_MAJOR=3
PYTHON_VERSION_MINOR=11
VENV_DIR="$SCRIPT_DIR/.venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
FLASK_SCRIPT="$SCRIPT_DIR/app.py"
OLLAMA_MODEL="llama3"

# --- Helper Functions ---
log() {
    COLOR_RESET='\033[0m'
    COLOR_GREEN='\033[0;32m'
    COLOR_YELLOW='\033[0;33m'
    COLOR_RED='\033[0;31m'
    COLOR_CYAN='\033[0;36m'
    
    case "$2" in
        "green") color=$COLOR_GREEN ;;
        "yellow") color=$COLOR_YELLOW ;;
        "red") color=$COLOR_RED ;;
        "cyan") color=$COLOR_CYAN ;;
        *) color=$COLOR_RESET ;;
    esac
    
    echo -e "$(date +'%H:%M:%S') | ${color}${1}${COLOR_RESET}"
}

# --- 1. Check for Python ---
log "Step 1: Checking for Python ${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}+..."
if ! command -v python3 &> /dev/null; then
    log "Python not found in PATH. Please install Python ${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR} or higher." "red"
    exit 1
fi

PY_VERSION_STRING=$(python3 --version)
PY_MAJOR=$(echo "$PY_VERSION_STRING" | cut -d' ' -f2 | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION_STRING" | cut -d' ' -f2 | cut -d. -f2)

if [ "$PY_MAJOR" -lt "$PYTHON_VERSION_MAJOR" ] || ([ "$PY_MAJOR" -eq "$PYTHON_VERSION_MAJOR" ] && [ "$PY_MINOR" -lt "$PYTHON_VERSION_MINOR" ]); then
    log "Found Python version ${PY_MAJOR}.${PY_MINOR}. Version ${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR} or higher is required." "red"
    exit 1
fi
log "Found compatible Python version: $PY_VERSION_STRING" "green"

# --- 1b. Check for NVIDIA CUDA ---
log "Step 1b: Checking for NVIDIA CUDA..."
if ! command -v nvidia-smi &> /dev/null; then
    log "Warning: 'nvidia-smi' command not found. GPU acceleration for PyTorch may fail." "yellow"
fi

# --- 1c. Check for Rust/Cargo ---
log "Step 1c: Checking for Rust (required for some dependencies)..."
if ! command -v cargo &> /dev/null; then
    log "Warning: Rust's build tool 'cargo' was not found in your PATH." "yellow"
    read -p "Do you want to attempt to install Rust now via rustup.rs? (y/n) " choice
    if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
        log "Installing Rust via rustup..."
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
        source "$HOME/.cargo/env"
        log "Rust has been installed. Please RESTART your terminal and run this script again." "green"
        exit 0
    else
        log "Please install Rust from https://rustup.rs/ and restart your terminal." "red"
        exit 1
    fi
fi

# --- 1d. Install Ollama ---
log "Step 1d: Checking for Ollama..."
if ! command -v ollama &> /dev/null; then
    log "Ollama not found. Attempting to install..." "yellow"
    curl -fsSL https://ollama.com/install.sh | sh
    log "Ollama installed successfully." "green"
fi
log "Ensuring Ollama model '$OLLAMA_MODEL' is available..."
ollama pull "$OLLAMA_MODEL"

# --- 2. Setup Virtual Environment ---
log "Step 2: Checking for virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    log "Virtual environment not found. Creating one at '$VENV_DIR'..." "yellow"
    python3 -m venv "$VENV_DIR"
    log "Virtual environment created." "green"
fi

source "$VENV_DIR/bin/activate"

# --- 3. Install Dependencies ---
log "Step 3: Installing dependencies from '$REQUIREMENTS_FILE'..."
pip install --upgrade pip
pip install -r "$REQUIREMENTS_FILE"
log "Dependencies installed successfully." "green"

# --- 3b. Verify PyTorch CUDA Availability ---
log "Step 3b: Verifying PyTorch can access the GPU..."
CUDA_CHECK_RESULT=$(python -c "import torch; print(torch.cuda.is_available())")
if [ "$CUDA_CHECK_RESULT" == "True" ]; then
    log "PyTorch successfully detected the NVIDIA GPU." "green"
else
    log "Warning: PyTorch is installed but cannot detect a compatible NVIDIA GPU. The app will run on the CPU." "yellow"
fi

# --- 4. Run the Application ---
log "Step 4: Launching the Flask application..."
if [ ! -f "$FLASK_SCRIPT" ]; then
    log "Flask application script '$FLASK_SCRIPT' not found!" "red"
    exit 1
fi

log "You can access the app at http://127.0.0.1:5000. Press CTRL+C in this window to stop the server." "cyan"
python "$FLASK_SCRIPT"