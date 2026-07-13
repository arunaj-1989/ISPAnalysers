import os
import json
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
import torch
import easyocr
import whisper
import ollama
import psutil

# Get the absolute path of the directory where this script is located
project_root = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=project_root
)
CORS(app)

# --- Configuration & Model Loading ---
UPLOAD_FOLDER = 'uploads'
HISTORY_FILE = 'history.json'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

print("INFO: Loading skill guidelines...")
with open(os.path.join(project_root, 'skill.md'), 'r', encoding='utf-8') as f:
    SKILL_GUIDELINES = f.read()

# Determine device
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print(f"INFO: Using device: {DEVICE}")

# --- Model Management ---
# Use a dictionary to cache loaded models
loaded_models = {}

def get_whisper_model(model_name: str):
    """Loads a Whisper model into memory, caching it for future use."""
    if model_name in loaded_models:
        print(f"INFO: Using cached Whisper model '{model_name}'.")
        return loaded_models[model_name]

    # Simple cache eviction: unload all other models to make space
    if loaded_models:
        print("INFO: Unloading existing models to free up memory.")
        loaded_models.clear()
        if DEVICE == 'cuda':
            torch.cuda.empty_cache()

    print(f"INFO: Loading Whisper model '{model_name}'...")
    model = whisper.load_model(model_name, device=DEVICE)
    print(f"INFO: Whisper model '{model_name}' loaded.")
    loaded_models[model_name] = model
    return model

# Pre-load the base model on startup
get_whisper_model("base")

print("INFO: Loading EasyOCR reader...")
ocr_reader = easyocr.Reader(['en'], gpu=(DEVICE == 'cuda'))

print("INFO: Flask app and models loaded successfully.")

# --- History Management ---
def load_history():
    """Loads the analysis history from the JSON file."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_history(data):
    """Saves the updated analysis history to the JSON file."""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

@app.route('/api/history', methods=['GET'])
def get_history():
    """Endpoint to retrieve the analysis history."""
    history = load_history()
    return jsonify(sorted(history, key=lambda x: x['timestamp'], reverse=True))

@app.route('/api/history/<item_id>', methods=['DELETE'])
def delete_history_item(item_id):
    """Deletes a specific history item by its ID."""
    history = load_history()
    item_found = any(item['id'] == item_id for item in history)
    if not item_found:
        return jsonify({"error": "Item not found"}), 404

    updated_history = [item for item in history if item['id'] != item_id]
    save_history(updated_history)
    return jsonify({"message": "Item deleted successfully"}), 200

@app.route('/')
def index():
    """Renders the main user interface."""
    return render_template('index.html')

@app.route('/api/clear-gpu-cache', methods=['POST'])
def clear_gpu_cache():
    """Endpoint to manually clear the CUDA cache and unload models."""
    if DEVICE == 'cuda':
        print("INFO: Clearing GPU cache and unloading all models.")
        loaded_models.clear()
        torch.cuda.empty_cache()
        # The default model will be reloaded on the next analysis request.
        return jsonify({"message": "GPU cache cleared and all models unloaded."}), 200
    return jsonify({"message": "Not using GPU, no cache to clear."}), 200

@app.route('/api/system-info')
def system_info():
    """Provides information about the system's CPU and GPU."""
    gpu_info = {}
    if DEVICE == 'cuda' and torch.cuda.is_available():
        torch.cuda.synchronize()
        free, total = torch.cuda.mem_get_info()
        gpu_info = {
            'name': torch.cuda.get_device_name(0),
            'total_memory': total,
            'free_memory': free,
        }

    return jsonify({
        'device': DEVICE,
        'gpu': gpu_info,
        'cpu': {
            'percent': psutil.cpu_percent(interval=0.2),
            'memory_percent': psutil.virtual_memory().percent,
        }
    })

@app.route('/api/process', methods=['POST'])
def process_files():
    """
    API endpoint to process an audio file and a screenshot.
    Streams progress updates using Server-Sent Events.
    """
    if 'audio' not in request.files or 'screenshot' not in request.files:
        return jsonify({"error": "Missing audio or screenshot file"}), 400

    # Get model name from the form, default to 'base'
    model_name = request.form.get('model', 'base')

    screenshot_file = request.files['screenshot']
    audio_file = request.files['audio']

    # Use unique filenames to avoid race conditions
    audio_filename = f"{uuid.uuid4()}_{audio_file.filename}"
    screenshot_filename = f"{uuid.uuid4()}_{screenshot_file.filename}"
    audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
    screenshot_path = os.path.join(app.config['UPLOAD_FOLDER'], screenshot_filename)
    audio_file.save(audio_path)
    screenshot_file.save(screenshot_path)

    def generate_progress():
        try:
            # 1. Process Screenshot with EasyOCR
            yield f"data: {json.dumps({'step': 'ocr', 'status': 'in_progress', 'message': 'Extracting text from image with EasyOCR...'})}\n\n"
            ocr_result = ocr_reader.readtext(screenshot_path, detail=0, paragraph=True)
            yield f"data: {json.dumps({'step': 'ocr', 'status': 'complete', 'result': ocr_result})}\n\n"

            # 2. Process Audio with Whisper
            yield f"data: {json.dumps({'step': 'transcribe', 'status': 'in_progress', 'message': f'Transcribing with Whisper ({model_name})...'})}\n\n"
            whisper_model = get_whisper_model(model_name)
            audio_transcription = whisper_model.transcribe(audio_path, fp16=(DEVICE == 'cuda'))
            transcription_text = audio_transcription['text']
            yield f"data: {json.dumps({'step': 'transcribe', 'status': 'complete', 'result': transcription_text})}\n\n"

            # 3. Process with Ollama
            yield f"data: {json.dumps({'step': 'summarize', 'status': 'in_progress', 'message': 'Generating AI summary with Ollama...'})}\n\n"
            analysis_request = f"""
**Customer Call Analysis Request**

**Audio Transcription:**
{transcription_text}

**Text Extracted from Screenshot:**
{' '.join(ocr_result)}
"""
            llm_prompt = f"""
You are an AI assistant for Interjet, a high-speed internet provider.
Your task is to analyze the provided customer interaction and generate a summary based on the company's standard operating procedures.

Follow these guidelines strictly:
{SKILL_GUIDELINES}

---
Here is the interaction data to analyze:
{analysis_request}
---

Please provide the English summary now."""
            llm_response = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': llm_prompt}])
            summary_text = llm_response['message']['content']
            yield f"data: {json.dumps({'step': 'summarize', 'status': 'complete', 'result': summary_text})}\n\n"

            # Save the results to history before finishing
            try:
                new_entry = {
                    "id": f"job-{int(datetime.now().timestamp())}",
                    "timestamp": datetime.now().isoformat(),
                    "audio_file": audio_file.filename if audio_file else "N/A",
                    "screenshot_file": screenshot_file.filename if screenshot_file else "N/A",
                    "summary": summary_text,
                    "transcription": transcription_text,
                    "ocr": ocr_result
                }
                history = load_history()
                history.append(new_entry)
                save_history(history)
            except Exception as e:
                print(f"Warning: Failed to save history entry. Reason: {e}")

            # 4. Signal completion
            yield f"data: {json.dumps({'step': 'done'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        finally:
            # 5. Clean up uploaded files
            os.remove(audio_path)
            os.remove(screenshot_path)

    return Response(generate_progress(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)