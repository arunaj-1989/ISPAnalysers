#!/bin/bash
#
# SYNOPSIS:
#   Sets up the environment and runs the Flask-based ISP Analyser application on Ubuntu.
#
# DESCRIPTION:
#   This script automates the setup and execution of the entire application. It performs the following steps:
#   1.  Validates that Python 3.11 or newer is installed.
#   2.  Checks for and helps install necessary build tools (build-essential, FFmpeg, Rust).
#   3.  Installs Ollama and pulls the required model if not present.
#   4.  Creates a Python virtual environment if it doesn't exist.
#   5.  Installs required packages from 'requirements.txt' (including LangChain/LangGraph agent stack).
#   6.  Verifies GPU support for PyTorch.
#   7.  Verifies AI agent dependencies can be imported.
#   8.  Launches the Flask web application.
#
# NOTES:
#   - Must be run from the root directory of the project.
#   - To stop the server, press CTRL+C in the terminal window.
#

set -e # Exit immediately if a command exits with a non-zero status.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Configuration ---
PYTHON_VERSION_MAJOR=3
PYTHON_VERSION_MINOR=11
VENV_DIR="$SCRIPT_DIR/.venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"
APP_SCRIPT="$SCRIPT_DIR/app.py"
OLLAMA_MODEL="phi3" # Match the model used in the README

# --- Helper Functions ---
log() {
    echo "[$(date +'%H:%M:%S')] $1"
}

log_color() {
    local color_code=$2
    local message=$1
    echo -e "[$(date +'%H:%M:%S')] \033[${color_code}m${message}\033[0m"
}

command_exists() {
    command -v "$1" &> /dev/null
}

# --- 1. Check for Python ---
log "Step 1: Checking for Python ${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}+..."
if ! command_exists python3; then
    log_color "Python 3 not found. Please install Python ${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR} or higher." "31" # Red
    exit 1
fi

PYTHON_EXE=$(command -v python3)
VERSION_STRING=$($PYTHON_EXE --version)
if [[ "$VERSION_STRING" =~ ([0-9]+)\.([0-9]+) ]]; then
    MAJOR=${BASH_REMATCH[1]}
    MINOR=${BASH_REMATCH[2]}
    if [ "$MAJOR" -lt "$PYTHON_VERSION_MAJOR" ] || ([ "$MAJOR" -eq "$PYTHON_VERSION_MAJOR" ] && [ "$MINOR" -lt "$PYTHON_VERSION_MINOR" ]); then
        log_color "Found Python version ${MAJOR}.${MINOR}. Version ${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR} or higher is required." "31" # Red
        exit 1
    fi
    log_color "Found compatible Python version at $PYTHON_EXE" "32" # Green
else
    log_color "Could not determine Python version from string: $VERSION_STRING" "31" # Red
    exit 1
fi

# --- 1b. Check for Build Tools & FFmpeg ---
log "Step 1b: Checking for build tools..."
if ! dpkg -s build-essential &>/dev/null; then
    log_color "Warning: 'build-essential' is not installed. It is required to compile some dependencies." "33" # Yellow
    read -p "Do you want to attempt to install it now? (y/n) " choice
    if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
        sudo apt-get update && sudo apt-get install -y build-essential
    else
        log_color "Please install 'build-essential' (sudo apt-get install build-essential) and run this script again." "31" # Red
        exit 1
    fi
fi
if ! command_exists ffmpeg; then
    log_color "Warning: 'ffmpeg' is not installed. It is required by Whisper for audio processing." "33" # Yellow
    read -p "Do you want to attempt to install it now? (y/n) " choice
    if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
        sudo apt-get update && sudo apt-get install -y ffmpeg
    else
        log_color "Please install 'ffmpeg' (sudo apt-get install ffmpeg) and run this script again." "31" # Red
        exit 1
    fi
fi

# --- 1c. Check for Rust/Cargo ---
log "Step 1c: Checking for Rust..."
if ! command_exists cargo; then
    log_color "Warning: Rust's build tool 'cargo' was not found." "33" # Yellow
    log_color "Some Python packages (like 'cryptography') may need Rust to compile." "33" # Yellow
    read -p "Do you want to attempt to install Rust now via rustup.rs? (y/n) " choice
    if [[ "$choice" == "y" || "$choice" == "Y" ]]; then
        log "Installing Rust via rustup..."
        curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
        source "$HOME/.cargo/env"
        log_color "Rust has been installed. 'cargo' is now in the PATH for this session." "32" # Green
    else
        log_color "Skipping Rust installation. Some dependencies might fail to build." "33" # Yellow
    fi
fi

# --- 1d. Install Ollama ---
log "Step 1d: Checking for Ollama..."
if ! command_exists ollama; then
    log_color "Ollama not found. Attempting to install..." "33" # Yellow
    curl -fsSL https://ollama.com/install.sh | sh
    log_color "Ollama installed successfully." "32" # Green
fi
log "Ensuring Ollama model '$OLLAMA_MODEL' is available..."
ollama pull "$OLLAMA_MODEL"

# --- 2. Setup Virtual Environment ---
log "Step 2: Checking for virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    log_color "Virtual environment not found. Creating one at '$VENV_DIR'..." "33" # Yellow
    "$PYTHON_EXE" -m venv "$VENV_DIR"
    log_color "Virtual environment created." "32" # Green
else
    log_color "Virtual environment already exists." "32" # Green
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# --- 3. Install Dependencies ---
log "Step 3: Installing dependencies from '$REQUIREMENTS_FILE'..."
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    log_color "'$REQUIREMENTS_FILE' not found. Cannot install dependencies." "31" # Red
    exit 1
fi

pip install --upgrade pip
pip install -r "$REQUIREMENTS_FILE"
log_color "Dependencies installed successfully." "32" # Green

# --- 3b. Verify PyTorch CUDA Availability ---
log "Step 3b: Verifying PyTorch can access the GPU..."
CUDA_CHECK_RESULT=$(python -c "import torch; print(torch.cuda.is_available())")
if [ "$CUDA_CHECK_RESULT" == "True" ]; then
    log_color "PyTorch successfully detected the NVIDIA GPU." "32" # Green
else
    log_color "Warning: PyTorch is installed but cannot detect a compatible NVIDIA GPU. The app will run on the CPU." "33" # Yellow
fi

# --- 3c. Verify AI Agent Dependencies ---
log "Step 3c: Verifying AI agent dependencies (LangChain/LangGraph)..."
if python -c "import langchain, langgraph, langchain_ollama" >/dev/null 2>&1; then
    log_color "AI agent dependencies are available." "32" # Green
else
    log_color "Failed to import one or more AI agent dependencies (langchain/langgraph/langchain-ollama)." "31" # Red
    log_color "Try re-running dependency installation or manually running: pip install -r $REQUIREMENTS_FILE" "31" # Red
    exit 1
fi

# --- 4. Run the Application ---
log "Step 4: Launching the Flask application..."

if [ ! -f "$APP_SCRIPT" ]; then
    log_color "Flask application script '$APP_SCRIPT' not found!" "31" # Red
    exit 1
fi

log_color "You can access the app at http://127.0.0.1:5000" "36" # Cyan
log_color "Press CTRL+C in this window to stop the server." "36" # Cyan
python "$APP_SCRIPT"

deactivate
log "Application stopped."