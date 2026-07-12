# ISP Analysers

This is a Streamlit web application designed for analyzing ISP data. It integrates powerful AI models to extract and process information from various sources.

## ✨ Features

-   **🤖 AI-Powered Analysis**: Uses a local Large Language Model (Ollama with `phi3`) to automatically categorize issues and suggest next steps.
-   **🎤 Audio Transcription**: Transcribes speech from audio files into text using `openai-whisper`.
-   **🖼️ Image-to-Text**: Extracts text from images (like screenshots of router errors or payment details) using `EasyOCR`.
-   **⚙️ GPU Accelerated**: Leverages NVIDIA GPUs via CUDA for fast and efficient audio transcription (Whisper) and text extraction (EasyOCR).

## Architecture Overview

The application uses a combination of technologies:

-   **Frontend**: `Streamlit` for the user interface.
-   **Speech-to-Text**: `openai-whisper` runs on the GPU for fast transcription and translation.
-   **Text Extraction**: `EasyOCR` handles text extraction from images.
-   **AI Analysis**: `Ollama` serves a local language model (`phi3`) for text analysis.
-   **Backend Logic**: A persistent background worker (`DecodeWorker`) processes audio independently of UI refreshes.

##  Prerequisites

### Hardware

-   **Server**: A server running a Linux distribution (Ubuntu is recommended).
-   **GPU**: An NVIDIA GPU with CUDA support is **required** for optimal performance.

### Software

-   **Python**: Version 3.11 is **required**. The dependencies for `openai-whisper` are not yet compatible with newer Python versions.
-   **NVIDIA Drivers & CUDA Toolkit**: The server must have the appropriate NVIDIA drivers and CUDA Toolkit (version 12.1 is recommended) installed.
-   **Ollama**: The Ollama service must be installed to run the local language models.
-   **FFmpeg**: A system utility required by Whisper for audio processing.

---

## 🚀 Installation Guide

### For Linux (Ubuntu)

1.  **Clone the Repository**: Get the project files onto your server.

    ```bash
    # Replace with your repository's URL
    git clone <your-repository-url>
    cd <repository-directory>
    ```

2.  **Run the Setup Script**: This script handles all dependencies, Python environment setup, and AI model downloads.

    ```bash
    chmod +x setup_server.sh
    ./setup_server.sh
    ```
    The script will guide you if any dependencies are missing and will set up everything required to run the application.

### For Windows

1.  **Clone the Repository**: Get the project files onto your machine.
2.  **Set PowerShell Execution Policy**: By default, Windows may prevent you from running local PowerShell scripts. To fix this, open a PowerShell terminal and run the following command once:

    ```powershell
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    ```

3.  **Run the Setup Script**: In the same PowerShell terminal, run the setup script. It will check for dependencies, set up the environment, and download all necessary models.

    ```powershell
    .\setup_server.ps1
    ```

## ▶️ Run the Application

After the setup script has completed successfully, you can start the application using the provided run scripts.

### For Linux (Ubuntu)

The `run_app.sh` script will activate the correct environment and launch the app.

```bash
chmod +x run_app.sh
./run_app.sh
```

Your application will be accessible in a web browser at `http://<your-server-ip>:8501`.

**Note**: You may need to configure your server's firewall to allow incoming traffic on port `8501`. For Ubuntu's `ufw`, the command would be `sudo ufw allow 8501`.