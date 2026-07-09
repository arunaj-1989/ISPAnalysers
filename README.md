# Tamil Speech Translation and Analysis Suite

This is a Streamlit web application designed for real-time and file-based translation of Tamil speech to English. It integrates powerful AI models to not only translate but also analyze the content of conversations for customer support scenarios.

## ✨ Features

-   **🎤 Live Translation**: Translates Tamil speech from a microphone into English text in real-time.
-   **📂 File-Based Translation**: Upload audio files (WAV, MP3, M4A) to get a full Tamil transcription and English translation.
-   **🤖 AI-Powered Call Analysis**: Uses a local Large Language Model (Ollama with `phi3`) to automatically categorize the customer's issue and suggest a next step based on predefined business logic (`skill.md`).
-   **🖼️ Screenshot Analysis**: For billing-related issues, it allows uploading a payment screenshot and uses a vision-capable model (`llava-phi3`) to perform OCR and verify payment details.
-   **⚙️ GPU Accelerated**: Leverages NVIDIA GPUs via CUDA for fast and efficient audio transcription with Whisper.

## Architecture Overview

The application uses a combination of technologies:

-   **Frontend**: `Streamlit` for the user interface.
-   **Live Audio**: `streamlit-webrtc` captures microphone input.
-   **Speech-to-Text**: `openai-whisper` runs on the GPU for fast transcription and translation.
-   **AI Analysis**: `Ollama` serves local language models (`phi3` for text, `llava-phi3` for vision) to provide insights.
-   **Backend Logic**: A persistent background worker (`DecodeWorker`) processes audio independently of UI refreshes.

##  Prerequisites

### Hardware

-   **Server**: A server running a Linux distribution (Ubuntu is recommended).
-   **GPU**: An NVIDIA GPU with CUDA support is **required**. The application is configured to run models on the GPU for performance.

### Software

-   **Python**: Version 3.9 or higher.
-   **NVIDIA Drivers & CUDA Toolkit**: The server must have the appropriate NVIDIA drivers and CUDA Toolkit (version 12.1 is recommended) installed.
-   **Ollama**: The Ollama service must be installed to run the local language models.
-   **FFmpeg**: A system utility required by Whisper for audio processing.

---

## 🚀 Hosting and Installation Guide

Follow these steps to deploy the application on your server.

### 1. Clone the Repository

First, get the project files onto your server.

```bash
# Replace with your repository's URL
git clone <your-repository-url>
cd <repository-directory>
```

### 2. Install System Dependencies

Update your package list and install `ffmpeg` and Python tools.

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv ffmpeg
```

### 3. Install and Configure Ollama

The application relies on local AI models served by Ollama.

```bash
# Install the Ollama service
curl -fsSL https://ollama.com/install.sh | sh

# Pull the required models. This will take some time and disk space.
ollama pull phi3
ollama pull llava-phi3
```

The Ollama service will start automatically and run in the background.

### 4. Set Up Python Environment

It's best practice to use a virtual environment to manage Python dependencies.

```bash
# Create a virtual environment
python3 -m venv .venv

# Activate the environment
source .venv/bin/activate
```

### 5. Install Python Libraries

Create a `requirements.txt` file with all the necessary libraries.

```ini
# requirements.txt
streamlit
openai-whisper
torch --index-url https://download.pytorch.org/whl/cu121
ollama
streamlit-webrtc
streamlit-autorefresh
numpy
scipy
```

Now, install them using pip.

```bash
pip install -r requirements.txt
```

### 6. Run the Application

A convenience script, `run_app.sh`, is provided to start the application correctly.

First, make the script executable:

```bash
chmod +x run_app.sh
```

Your application will be accessible in a web browser at `http://<your-server-ip>:8501`.

**Note**: You may need to configure your server's firewall to allow incoming traffic on port `8501`. For Ubuntu's `ufw`, the command would be `sudo ufw allow 8501`.