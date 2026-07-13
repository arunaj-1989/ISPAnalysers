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

2.  **Run the Orchestration Script**: This single script handles all dependencies, Python environment setup, AI model downloads, and launches the application.

    ```bash
    chmod +x orchestration.sh
    ./orchestration.sh
    ```
    The script will guide you if any dependencies are missing, set up everything required, and start the application server.

### For Windows

1.  **Clone the Repository**: Get the project files onto your machine.
2.  **Set PowerShell Execution Policy**: By default, Windows may prevent you from running local PowerShell scripts. To fix this, open a PowerShell terminal and run the following command once:

    ```powershell
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    ```

3.  **Run the Orchestration Script**: In the same PowerShell terminal, run the orchestration script. It will check for dependencies, set up the environment, download all necessary models, and launch the application.

    ```powershell
    .\orchestration.ps1
    ```

Your application will be accessible in a web browser at `http://<your-server-ip>:8501`.

**Note**: You may need to configure your server's firewall to allow incoming traffic on port `8501`. For Ubuntu's `ufw`, the command would be `sudo ufw allow 8501`.

---

## 🔌 Using the API

Beyond the Streamlit user interface, the application exposes a REST API endpoint for programmatic analysis. This allows you to integrate the ISP analysis capabilities into other systems or scripts.

The primary endpoint is `/analyze`, which accepts `multipart/form-data` POST requests.

**Endpoint**: `POST /analyze`
**Port**: `5000` (default for Flask)

### Request Body

You must provide at least one audio file. You can optionally include one or more image files for evidence analysis.

-   `audio`: The customer call audio file (e.g., `.mp3`, `.wav`, `.m4a`).
-   `image`: An image file for evidence (e.g., a screenshot of router lights or a payment confirmation). You can provide multiple `image` parts in a single request.

### Example API Call with `curl`

This example sends one audio file and two image files for analysis.

```bash
curl -X POST http://<your-server-ip>:5000/analyze \
  -F "audio=@/path/to/customer_call.mp3" \
  -F "image=@/path/to/router_lights.jpg" \
  -F "image=@/path/to/payment_screenshot.png"
```

### Example API Call with Python

This example shows how to call the API using the `requests` library in Python.

```python
import requests

# The server's IP address and port
url = "http://<your-server-ip>:5000/analyze"

# Define the paths to your files
audio_file_path = "/path/to/customer_call.mp3"
image_files_paths = [
    "/path/to/router_lights.jpg",
    "/path/to/payment_screenshot.png"
]

# Prepare the files for the multipart request
files = [("image", (open(path, "rb"))) for path in image_files_paths]
files.append(("audio", open(audio_file_path, "rb")))

try:
    response = requests.post(url, files=files)
    response.raise_for_status()  # Raise an exception for bad status codes
    
    # Print the JSON response from the server
    print(response.json())

except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")

finally:
    # Ensure all files are closed
    for _, file_tuple in files:
        file_tuple.close()
```

### Example JSON Response

The API will return a JSON object containing the transcription and the final analysis.

```json
{
  "transcription": "Hello my internet is not working, the light is red...",
  "analysis": {
    "customer_name": "N/A",
    "issue_category": "Connectivity Issue",
    "key_info": {
      "symptoms": ["internet not working", "light is red"]
    },
    "evidence_summary": "Image analysis of 'router_lights.jpg' shows a red light, indicating a connection problem.",
    "recommendation": "Customer is facing a connectivity issue. Router's 'Internet' light is red. A restart did not solve the problem. Recommended next step: Schedule a technician visit."
  }
}
```