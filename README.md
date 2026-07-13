# Interjet Support Analyser

This is a web application designed for analyzing ISP customer support interactions. It integrates powerful AI models to extract and process information from audio calls and screenshots, providing a comprehensive summary and audit trail.

## ✨ Features

-   **Modern Web UI**: A responsive frontend built with Flask and Bootstrap, featuring a dark/light theme switcher.
-   **🤖 Configurable AI Analysis**: Uses local Large Language Models via Ollama to automatically categorize issues and suggest next steps. The model used for analysis can be configured in the settings.
-   **🎤 Audio Transcription**: Transcribes speech from audio files into text using `openai-whisper`, with selectable model sizes for balancing speed and accuracy.
-   **🖼️ Image-to-Text (OCR)**: Extracts text from images (like payment screenshots) using `EasyOCR`.
-   **⚙️ GPU Accelerated**: Leverages NVIDIA GPUs via CUDA for fast and efficient AI processing.
-   **📊 Interactive Dashboard**: Review, search, sort, and filter the entire analysis history. Includes an audit-friendly table view with a CSV export option.
-   **🔧 Centralized Settings**: A dedicated page to configure default AI models and monitor real-time hardware utilization (GPU, CPU, RAM, Storage).
-   **🚀 Real-time Progress**: The analysis workflow provides live progress updates using Server-Sent Events (SSE).

## Architecture Overview

The application uses a combination of technologies:

-   **Backend**: A `Flask` server written in Python handles file uploads, AI processing, and API endpoints.
-   **Frontend**: A custom single-page interface built with `HTML`, `JavaScript`, and `Bootstrap`.
-   **Speech-to-Text**: `openai-whisper` for audio transcription.
-   **Text Extraction (OCR)**: `EasyOCR` for image-to-text conversion.
-   **AI Analysis**: `Ollama` serves local language models (e.g., Llama 3, Phi-3) for summarization.
-   **Data Persistence**: Analysis history is stored in a local `history.json` file, and model configurations are saved in `config.json`.

```mermaid
graph TD
    subgraph "User`s Browser"
        A[Frontend <br> (HTML/JS/Bootstrap)]
    end

    subgraph "Backend Server"
        B[Flask App <br> (app.py)]
        
        subgraph "AI/ML Models"
            C[EasyOCR <br> (Image to Text)]
            D[Whisper <br> (Audio to Text)]
            E[Ollama <br> (LLM/SLM for Summary)]
        end

        subgraph "Data Storage"
            F[config.json <br> (Settings)]
            G[history.json <br> (Audit Trail)]
        end
    end

    A -- "File Uploads & API Requests" --> B
    B -- "Process Image" --> C
    B -- "Transcribe Audio" --> D
    B -- "Generate Summary" --> E
    B -- "Read/Write Settings" --> F
    B -- "Read/Write History" --> G
    B -- "Serves UI & Streams Results" --> A
```

##  Prerequisites

### Hardware

-   **Server**: A server running a Linux or Windows distribution.
-   **GPU**: An NVIDIA GPU with CUDA support is **required** for optimal performance.

### Software

-   **Python**: Version 3.11 is **required**. The dependencies for `openai-whisper` are not yet compatible with newer Python versions.
-   **NVIDIA Drivers & CUDA Toolkit**: The server must have the appropriate NVIDIA drivers and CUDA Toolkit (version 12.1 is recommended) installed.
-   **Ollama**: The Ollama service must be installed to run the local language models.
-   **FFmpeg**: A system utility required by Whisper for audio processing.

---

## 🚀 Local Installation & Setup

1.  **Clone the Repository**:
    ```bash
    git clone <your-repository-url>
    cd ISPAnalysers
    ```

2.  **Create a Virtual Environment**:
    ```bash
    python -m venv .venv
    ```

3.  **Activate the Environment**:
    -   **Windows**: `.\.venv\Scripts\activate`
    -   **Linux/macOS**: `source .venv/bin/activate`

4.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: You will need to create a `requirements.txt` file containing libraries like `flask`, `torch`, `easyocr`, `openai-whisper`, `ollama`, `psutil`, etc.)*

5.  **Run the Application**:
    ```bash
    python app.py
    ```
    The application will be accessible at `http://127.0.0.1:5000`.

---

## 🔌 Using the API

The application exposes a REST API endpoint for programmatic analysis, which streams progress and results via Server-Sent Events (SSE).

**Endpoint**: `POST /api/process`
**Port**: `5000` (default for Flask)

### Request Body

You must provide at least one file (`audio` or `screenshot`). You can also specify which AI models to use.

-   `audio` (optional): The customer call audio file (e.g., `.mp3`, `.wav`).
-   `screenshot` (optional): An image file for evidence (e.g., a payment confirmation).
-   `model` (optional): The name of the Whisper model to use (e.g., `base`, `small`).
-   `agent_model` (optional): The name of the Ollama agent model to use (e.g., `llama3`, `phi3:mini`).

### Example API Call with `curl`

This example sends an audio file and a screenshot for analysis.
```bash
curl -N -X POST http://127.0.0.1:5000/api/process \
  -F "audio=@/path/to/renewal.wav" \
  -F "screenshot=@/path/to/payment.png"
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