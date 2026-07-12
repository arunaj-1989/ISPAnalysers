#!/bin/bash

# ==============================================================================
# Setup and Run Script for ISP Analysers App on Ubuntu
# ==============================================================================
# This script automates the setup and execution of the ISP Analysers app.
# It performs the following steps:
# 1. Checks for and installs system dependencies (Python 3.11, ffmpeg).
# 2. Checks for and installs Ollama and pulls the required model.
# 3. Creates a Python virtual environment if it doesn't exist.
# 4. Installs Python dependencies and verifies GPU support for PyTorch.
# 5. Pre-caches AI models to avoid first-run delays.
# 6. Starts the Streamlit application, making it available on the network.
#
# Usage: ./Start-Server.sh
# ==============================================================================

# Exit immediately if a command exits with a non-zero status.
set -e

# Navigate to the script's directory to ensure correct file paths.
cd "$(dirname "$0")"

# --- 1. System Dependencies ---
if ! command -v python3.11 &> /dev/null; then
    echo "› Python 3.11 not found. Installing system dependencies..."
    sudo apt-get update
    sudo apt-get install -y python3.11 python3.11-venv python3.11-pip ffmpeg
fi

# --- 2. Install Ollama ---
if ! command -v ollama &> /dev/null; then
    echo "› Ollama not found. Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    echo "› Ollama installed. The service will start on boot."
fi

# --- 3. Pull Ollama Models ---
# This command is idempotent; it will only download if the model is missing or updated.
echo "› Ensuring Ollama model 'phi3' is available..."
ollama pull phi3

# --- 4. Python Environment Setup ---
if [ ! -d ".venv" ]; then
    echo "› Creating Python virtual environment in '.venv'..."
    python3.11 -m venv .venv

    echo "› Activating virtual environment..."
    source .venv/bin/activate

    # --- 5. Install Python Libraries ---
    echo "› Upgrading core packaging tools..."
    pip install --upgrade pip setuptools wheel

    echo "› Installing application dependencies from requirements.txt..."
    pip install -r requirements.txt

    # --- 5a. Verify PyTorch CUDA ---
    echo "› Verifying PyTorch can access the GPU..."
    if python3.11 -c "import torch; exit(0) if torch.cuda.is_available() else exit(1)"; then
        echo "› PyTorch successfully detected the NVIDIA GPU."
    else
        echo "› Warning: PyTorch cannot detect a compatible NVIDIA GPU. The application will run in CPU mode." >&2
        echo "  Please check your NVIDIA drivers and CUDA installation if you intended to use a GPU." >&2
    fi

    # --- 5b. Pre-cache AI Models ---
    echo "› Pre-caching Whisper models to avoid first-run delays..."
    python3.11 pre_cache_models.py

    echo "› Pre-caching EasyOCR models to avoid first-run delays..."
    python3.11 pre_cache_ocr_models.py

    echo "› Setup complete."
else
    echo "› Activating existing Python virtual environment..."
    source .venv/bin/activate
fi

# --- 6. Run the Application ---
echo "› Starting Streamlit application on port 8501..."
echo "› Access it at http://<your-server-ip>:8501"

# The server.address=0.0.0.0 makes it accessible from other machines on the network.
# KMP_DUPLICATE_LIB_OK=TRUE is set to prevent potential DLL conflicts with MKL.
KMP_DUPLICATE_LIB_OK=TRUE streamlit run Home.py --server.address=0.0.0.0 --server.port=8501