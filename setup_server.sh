#!/bin/bash

# ==============================================================================
# Setup Script for Tamil Speech Translation App on Ubuntu
# ==============================================================================
# This script automates the complete setup of the Streamlit application by:
# 1. Installing system dependencies.
# 2. Installing Ollama and downloading the required models.
# 3. Creating a Python virtual environment and installing all libraries.
# 4. Providing instructions to run the application.
# ==============================================================================

# Exit immediately if a command exits with a non-zero status.
set -e

# --- 1. System Dependencies ---
echo "› Updating system packages and installing dependencies..."
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv ffmpeg

# --- 2. Install Ollama ---
echo "› Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

echo "› Ollama installed. Starting Ollama service..."
# The install script should start it, but this ensures it's running.
# Note: On some systems, you might need to restart your terminal or source your shell profile.
# The Ollama service will start automatically on boot.

# --- 3. Pull Ollama Models ---
echo "› Pulling required Ollama models. This may take some time..."
ollama pull phi3
ollama pull llava-phi3
echo "› Ollama models have been downloaded."

# --- 4. Python Environment Setup ---
echo "› Creating Python virtual environment in '.venv'..."
python3 -m venv .venv

echo "› Activating virtual environment..."
source .venv/bin/activate

# --- 5. Install Python Libraries ---
echo "› Installing Python libraries from requirements.txt..."

pip install -r requirements.txt

echo "› Python libraries installed successfully."

# --- 5a. Pre-cache Whisper Models ---
echo "› Pre-caching Whisper models to avoid first-run delays..."
# Run the Python script to download and cache the models
python3 pre_cache_models.py

# --- 6. Final Instructions ---
echo ""
echo "✅ Setup Complete!"
echo ""
echo "To run your application:"
echo "1. Make the run script executable:"
echo "   chmod +x run_app.sh"
echo "2. Start the application:"
echo "   ./run_app.sh"
echo ""
echo "The app will be available at http://<your-server-ip>:8501"
echo "You may need to open port 8501 in your server's firewall."