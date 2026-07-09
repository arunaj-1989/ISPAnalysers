#!/bin/bash

# ==============================================================================
# Run Script for Tamil Speech Translation App
# ==============================================================================
# This script activates the Python virtual environment and starts the
# Streamlit application, making it accessible on the local network.
#
# Usage: ./run_app.sh
# ==============================================================================

# Exit immediately if a command exits with a non-zero status.
set -e

# Navigate to the script's directory to ensure correct file paths
cd "$(dirname "$0")"

# --- 1. Activate Virtual Environment ---
echo "› Activating Python virtual environment..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Error: Virtual environment '.venv' not found." >&2
    echo "Please run the setup_server.sh script first." >&2
    exit 1
fi

# --- 2. Run the Application ---
echo "› Starting Streamlit application on port 8501..."
echo "› Access it at http://<your-server-ip>:8501"

# The server.address=0.0.0.0 makes it accessible from other machines on the network.
streamlit run Home.py --server.address=0.0.0.0 --server.port=8501