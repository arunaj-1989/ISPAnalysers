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
MODEL_NAMES_FILE = 'model_names.json'
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

def load_model_names():
    """Loads the available model names and descriptions from JSON file."""
    try:
        with open(MODEL_NAMES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return empty lists on error
        return {"agent_models": [], "whisper_models": []}

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

@app.route('/api/config', methods=['GET', 'POST'])
def app_config():
    """Endpoint to get or set application configuration."""
    if request.method == 'POST':
        # Load current model data
        model_config = load_model_names()
        # Update only the default keys from the request
        new_defaults = request.json
        model_config['default_agent_model'] = new_defaults.get('default_agent_model', model_config.get('default_agent_model'))
        model_config['default_whisper'] = new_defaults.get('default_whisper', model_config.get('default_whisper'))
        # Save the entire file back
        with open(MODEL_NAMES_FILE, 'w', encoding='utf-8') as f:
            json.dump(model_config, f, indent=4)
        return jsonify({"message": "Configuration saved successfully."}), 200
    else:
        # Return only the default model keys
        config = load_model_names()
        return jsonify({
            "default_agent_model": config.get("default_agent_model"),
            "default_whisper": config.get("default_whisper")
        })

@app.route('/api/available-models', methods=['GET'])
def available_models():
    """Endpoint to get the list of available models for UI dropdowns."""
    return jsonify(load_model_names())

@app.route('/api/models-status', methods=['GET'])
def models_status():
    """Checks and returns the status of available AI models."""
    agent_status, whisper_status = {}, {}
    model_names = load_model_names()
    agent_models_to_check = [m['id'] for m in model_names.get('agent_models', [])]
    whisper_models_to_check = [m['id'] for m in model_names.get('whisper_models', [])]

    # Helper function to ensure everything has a tag for exact matching
    def normalize_tag(name):
        if name and ':' not in name:
            return f"{name}:latest"
        return name

    # --- Check Ollama Models ---
    try:
        response = ollama.list()
        ollama_models_on_disk = set()
        
        # Handle dictionary response (Older ollama-python versions)
        if isinstance(response, dict):
            if 'error' in response:
                raise Exception(response['error'])
            ollama_models_on_disk = {model.get('name', model.get('model')) for model in response.get('models', [])}
        
        # Handle object response (Newer ollama-python versions >= 0.2.0)
        else:
            ollama_models_on_disk = {model.model for model in getattr(response, 'models', [])}

        # Normalize all disk models to 'name:tag' format
        normalized_disk_models = {normalize_tag(m) for m in ollama_models_on_disk if m}

        if not normalized_disk_models:
            # If no models are on disk, mark all as not_downloaded
            for model_name in agent_models_to_check:
                agent_status[model_name] = {"status": "not_downloaded"}
        else:
            for model_name in agent_models_to_check:
                # Direct exact check against normalized strings
                is_downloaded = normalize_tag(model_name) in normalized_disk_models
                agent_status[model_name] = {"status": "downloaded" if is_downloaded else "not_downloaded"}
            
    except Exception as e:
        # Broad exception catches httpx.ConnectError if the Ollama daemon isn't running
        print(f"Warning: Could not check Ollama model status. Error: {e}")
        for model_name in agent_models_to_check:
            agent_status[model_name] = {"status": "unavailable", "error": "Ollama service not running"}

    # --- Check Whisper Models ---
    try:
        whisper_cache_path = os.path.join(os.path.expanduser("~"), ".cache", "whisper")
        os.makedirs(whisper_cache_path, exist_ok=True)
        for model_name in whisper_models_to_check:
            model_file = os.path.join(whisper_cache_path, f"{model_name}.pt")
            whisper_status[model_name] = {"status": "downloaded" if os.path.exists(model_file) else "not_downloaded"}
    except Exception as e:
        print(f"Warning: Could not check Whisper model status. Error: {e}")
        for model_name in whisper_models_to_check:
            whisper_status[model_name] = {"status": "unavailable", "error": "File system error"}

    return jsonify({
        "agent_models": agent_status,
        "whisper_models": whisper_status
    })

@app.route('/api/models/agent/<path:model_name>', methods=['DELETE'])
def delete_agent_model(model_name):
    """Deletes a locally cached Ollama model."""
    try:
        print(f"INFO: Deleting Ollama model '{model_name}'...")
        ollama.delete(model_name)
        print(f"INFO: Model '{model_name}' deleted successfully.")
        return jsonify({"message": f"Model '{model_name}' deleted successfully."}), 200
    except Exception as e:
        # Handle cases where the model doesn't exist or Ollama service is down
        error_message = f"Failed to delete Ollama model '{model_name}': {str(e)}"
        print(f"ERROR: {error_message}")
        return jsonify({"error": error_message}), 500

@app.route('/api/models/whisper/<model_name>', methods=['DELETE'])
def delete_whisper_model(model_name):
    """Deletes a locally cached Whisper model file."""
    try:
        whisper_cache_path = os.path.join(os.path.expanduser("~"), ".cache", "whisper")
        model_file = os.path.join(whisper_cache_path, f"{model_name}.pt")
        if os.path.exists(model_file):
            print(f"INFO: Deleting Whisper model '{model_name}' from '{model_file}'...")
            os.remove(model_file)
            print(f"INFO: Model '{model_name}' deleted successfully.")
            return jsonify({"message": f"Whisper model '{model_name}' deleted."}), 200
        return jsonify({"error": "Model file not found."}), 404
    except Exception as e:
        return jsonify({"error": f"Failed to delete Whisper model: {str(e)}"}), 500

@app.route('/api/cache-models', methods=['POST'])
def cache_models():
    """Streams the progress of caching the default models."""
    data = request.json
    agent_models = data.get('agent_models', [])
    whisper_models = data.get('whisper_models', [])

    if not agent_models and not whisper_models:
        return Response(json.dumps({'status': 'error', 'message': 'No models selected for caching.'}), mimetype='application/json', status=400)

    def generate_cache_progress():
        try:
            total_models = len(agent_models) + len(whisper_models)
            completed_models = 0

            # 1. Pull Ollama models
            for agent_model in agent_models:
                yield f"data: {json.dumps({'status': 'in_progress', 'message': f'Pulling agent model: {agent_model}...', 'progress': 0})}\n\n"
                try:
                    for progress in ollama.pull(agent_model, stream=True):
                        percentage = 0
                        # Ensure 'total' and 'completed' exist and are not None before calculating percentage
                        total = progress.get("total")
                        completed = progress.get("completed")
                        if total is not None and completed is not None and total > 0:
                            percentage = round((completed / total) * 100)
                        status_message = progress.get('status', f'Pulling {agent_model}...')
                        if 'completed' in progress and 'total' in progress:
                            status_message = f"Downloading: {round(progress['completed']/1e9, 2)}GB / {round(progress['total']/1e9, 2)}GB"
                        yield f"data: {json.dumps({'status': 'in_progress', 'message': status_message, 'progress': percentage})}\n\n"
                    completed_models += 1
                except Exception as e:
                    yield f"data: {json.dumps({'status': 'error', 'message': f'Failed to pull {agent_model}: {str(e)}'})}\n\n"

            # 2. Load Whisper models (which also downloads if not present)
            for whisper_model_name in whisper_models:
                yield f"data: {json.dumps({'status': 'in_progress', 'message': f'Caching Whisper model: {whisper_model_name}...', 'progress': 100})}\n\n"
                get_whisper_model(whisper_model_name)
                completed_models += 1

            yield f"data: {json.dumps({'status': 'complete', 'message': f'Successfully cached {completed_models}/{total_models} selected models.'})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"
    return Response(generate_cache_progress(), mimetype='text/event-stream')

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

    v_mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    return jsonify({
        'device': DEVICE,
        'gpu': gpu_info,
        'cpu': {
            'percent': psutil.cpu_percent(interval=None),
        },
        'ram': {
            'total': v_mem.total, 'available': v_mem.available, 'percent': v_mem.percent
        },
        'storage': {
            'total': disk.total, 'used': disk.used, 'percent': disk.percent
        }
    })

@app.route('/api/process', methods=['POST'])
def process_files():
    """
    API endpoint to process an audio file and a screenshot.
    Streams progress updates using Server-Sent Events.
    """
    if 'audio' not in request.files and 'screenshot' not in request.files:
        return jsonify({"error": "Please upload at least one file (audio or screenshot)."}), 400

    # Load defaults from the unified model config
    app_config = load_model_names()
    model_name = request.form.get('model', app_config.get('default_whisper', 'base'))
    agent_model = request.form.get('agent_model', app_config.get('default_agent_model', 'llama3'))

    screenshot_file = request.files.get('screenshot')
    audio_file = request.files.get('audio')

    # Use unique filenames to avoid race conditions
    audio_path = None
    screenshot_path = None

    if audio_file and audio_file.filename:
        audio_filename = f"{uuid.uuid4()}_{audio_file.filename}"
        audio_path = os.path.join(app.config['UPLOAD_FOLDER'], audio_filename)
        audio_file.save(audio_path)

    if screenshot_file and screenshot_file.filename:
        screenshot_filename = f"{uuid.uuid4()}_{screenshot_file.filename}"
        screenshot_path = os.path.join(app.config['UPLOAD_FOLDER'], screenshot_filename)
        screenshot_file.save(screenshot_path)

    def generate_progress():
        ocr_result = []
        transcription_text = ""
        try:
            # 1. Process Screenshot with EasyOCR
            if screenshot_path:
                yield f"data: {json.dumps({'step': 'ocr', 'status': 'in_progress', 'message': 'Extracting text from image with EasyOCR...'})}\n\n"
                ocr_result = ocr_reader.readtext(screenshot_path, detail=0, paragraph=True)
                yield f"data: {json.dumps({'step': 'ocr', 'status': 'complete', 'result': ocr_result})}\n\n"
            else:
                yield f"data: {json.dumps({'step': 'ocr', 'status': 'skipped'})}\n\n"

            # 2. Process Audio with Whisper
            if audio_path:
                yield f"data: {json.dumps({'step': 'transcribe', 'status': 'in_progress', 'message': f'Transcribing with Whisper ({model_name})...'})}\n\n"
                whisper_model = get_whisper_model(model_name)
                audio_transcription = whisper_model.transcribe(audio_path, fp16=(DEVICE == 'cuda'))
                transcription_text = audio_transcription['text']
                yield f"data: {json.dumps({'step': 'transcribe', 'status': 'complete', 'result': transcription_text})}\n\n"
            else:
                yield f"data: {json.dumps({'step': 'transcribe', 'status': 'skipped'})}\n\n"

            # 3. Process with Ollama
            yield f"data: {json.dumps({'step': 'summarize', 'status': 'in_progress', 'message': f'Generating AI summary with {agent_model}...'})}\n\n"
            analysis_request = f"""
**Customer Call Analysis Request**

**Audio Transcription:**
{transcription_text if transcription_text else "N/A"}

**Text Extracted from Screenshot:**
{' '.join(ocr_result) if ocr_result else "N/A"}
"""
            llm_prompt = f"""
You are an AI assistant for Interjet, a high-speed internet provider.
Your task is to analyze the provided customer interaction and generate a summary based on the company's standard operating procedures.
If only a screenshot is provided, focus on analyzing the details from the image.
If only audio is provided, focus on the transcription.
If both are provided, use both as context.

Follow these guidelines strictly:
{SKILL_GUIDELINES}

---
Here is the interaction data to analyze:
{analysis_request}
---

Please provide the English summary now. Structure your response using the following markdown format, ensuring each field is on a new line:
**Customer Name:** [Customer's name from audio or screenshot, or N/A]
**Issue Category:** [The categorized issue]
**Key Information:** [Other key details from the call or text, NOT related to the payment]
**Payment Date & Time:** [Date and Time from screenshot, e.g., "July 13, 2026, 11:03 AM", or N/A]
**Payment Amount:** [Amount from screenshot as a number only, e.g., 599, or N/A]
**Payer Details:** [Payer name or UPI ID from screenshot, or N/A]
**Payee Details:** [Payee name or UPI ID from screenshot, or N/A]
**UPI Transaction ID:** [Transaction ID from screenshot, or N/A]
**Recommended Next Step:** [The recommended next step based on the SOPs]

Example:
**Customer Name:** Sri Lalitha
**Issue Category:** Billing Issue / Account Deactivated
**Key Information:** Account was deactivated despite a recent payment.
**Payment Date & Time:** July 13, 2026, 11:03 AM
**Payment Amount:** 599
**Payer Details:** Sri Lalitha (XXXXXX14II)
**Payee Details:** HELPDESK INDIA IT SEVICES (interjet@oksbi)
**UPI Transaction ID:** T2607131103267467683715
**Recommended Next Step:** Escalate to billing to verify payment and reactivate the account.
"""
            llm_response = ollama.chat(model=agent_model, messages=[{'role': 'user', 'content': llm_prompt}])
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
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
            if screenshot_path and os.path.exists(screenshot_path):
                os.remove(screenshot_path)
            
            # 6. Clear GPU cache and unload models after analysis
            if DEVICE == 'cuda':
                yield f"data: {json.dumps({'step': 'cleanup', 'status': 'in_progress', 'message': 'GPU cache cleared and all models unloaded.'})}\n\n"
                loaded_models.clear()
                torch.cuda.empty_cache()

    return Response(generate_progress(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)