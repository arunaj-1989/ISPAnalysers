import streamlit as st
import torch
import tempfile
import time
from utils import get_worker, SOURCE_LANGUAGE
import re
from pathlib import Path

try:
    import ollama
    import easyocr
    OLLAMA_AVAILABLE = True

except ImportError:
    OLLAMA_AVAILABLE = False
    easyocr = None # type: ignore

ocr_model = None

def get_ocr_model():
    """Initializes and returns the PaddleOCR model, caching it in a global variable."""
    global ocr_model
    if ocr_model is not None:
        return ocr_model

    try:
        st.info("Loading OCR model (EasyOCR)...")
        use_gpu = torch.cuda.is_available()
        ocr_model = easyocr.Reader(['en'], gpu=use_gpu, model_storage_directory=str(Path.home() / ".EasyOCR" / "model"))
        device = "GPU" if use_gpu else "CPU"
        st.info(f"OCR model loaded on {device}.")
        return ocr_model
    except Exception as e:
        st.error(f"Failed to initialize EasyOCR. It will be disabled. Error: {e}")
        return None

def extract_text_from_image(ocr_instance, image_bytes: bytes) -> str:
    """
    Uses EasyOCR to extract text from an image.
    """
    with st.spinner("Performing OCR on screenshot..."):
        try:
            if ocr_instance is None:
                raise RuntimeError("EasyOCR is not available or failed to initialize.")
                
            result = ocr_instance.readtext(image_bytes, detail=0, paragraph=True)
            if not result:
                return ""
            
            return "\n".join(result)
        except Exception as e:
            st.error(f"An error occurred during OCR with EasyOCR: {e}")
            return ""


def categorize_and_suggest_fix(translated_text: str, worker, screenshot_text: str | None = None, model_name: str | None = None) -> (str, str):
    """
    Uses an Ollama SLM to categorize the text and provide a suggested fix
    based on the skill.md file.
    """
    try:
        # model_name is passed from the main thread to reload whisper later
        skill_content = Path("skill.md").read_text(encoding="utf-8")
    except FileNotFoundError:
        st.error("The `skill.md` file was not found. Please ensure it exists in the root directory.")
        return "Error", "The `skill.md` file was not found."

    screenshot_context = ""
    if screenshot_text:
        screenshot_context = f"""
    Additionally, the user has provided a screenshot. Here is the text extracted from it:
    ---
    {screenshot_text}
    ---
    Use the information from this screenshot as supplementary evidence to support your analysis, especially for issues related to billing, payments, or router errors.
    """

    prompt = f"""
    You are an expert ISP support agent assistant. Your task is to analyze a customer complaint and provide a category and a suggested fix based on a set of standard operating procedures.

    Here are the Standard Operating Procedures (SOPs) from the skill file:
    ---
    {skill_content}
    ---
    Here is the English translation of the customer conversation:
    ---
    {translated_text}
    ---
    {screenshot_context}

    Based on the SOPs and the conversation, please perform the following:
    1.  **Categorize the issue:** Choose the most appropriate category from the "Issue Categories" section of the SOPs.
    2.  **Suggest a fix:** Provide a clear, step-by-step fix based on the troubleshooting steps or procedures in the SOPs for the identified category.

    Provide your response in the following format, and nothing else:
    Category: [The category you identified]
    Fix: [The suggested fix]
    """

    try:
        # Unload Whisper model to free up VRAM for Ollama
        with worker.lock:
            if worker.model is not None:
                st.info("Unloading Whisper model to free up VRAM for local AI...")
                # Move model to CPU and delete to free VRAM
                worker.model = worker.model.to('cpu')
                del worker.model
                worker.model = None
                torch.cuda.empty_cache()

        with st.spinner("Asking the local AI for suggestions..."):
            response = ollama.chat(
                model='phi3',  # This should match the model the user has pulled
                messages=[{'role': 'user', 'content': prompt}],
            )
            response_text = response['message']['content']

        # Parse the response
        category_match = re.search(r"Category: (.*)", response_text)
        fix_match = re.search(r"Fix: (.*)", response_text, re.DOTALL)

        category = category_match.group(1).strip() if category_match else "Uncategorized"
        fix = fix_match.group(1).strip() if fix_match else "Could not determine a fix from the local AI's response."

        return category, fix

    except Exception as e:
        st.error(f"Could not connect to Ollama. Please ensure the Ollama application is running and you have pulled the 'phi3' model by running `ollama pull phi3` in your terminal.")
        return "Error", str(e)
    finally:
        # Reload the whisper model
        if model_name:
            st.info("Reloading Whisper model...")
            with worker.lock:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                worker.load_model(model_name, device)

def transcribe_robust(model, audio_path, **kwargs):
    """
    Wrapper for whisper's transcribe function that retries with more stable
    parameters if a PyTorch error occurs.
    """
    try:
        return model.transcribe(audio_path, **kwargs)
    except Exception as e:
        if "key.size(1) == value.size(1)" in str(e):
            st.warning("A PyTorch error occurred during transcription. Retrying with more stable settings (fp32)...")
            kwargs["fp16"] = False
            return model.transcribe(audio_path, **kwargs)
        else:
            raise e

def get_ollama_device_info(model_name: str) -> str:
    """Checks if an Ollama model is loaded on CPU or GPU."""
    if not OLLAMA_AVAILABLE:
        return "N/A"
    try:
        details = ollama.show(model_name)
        # The presence of 'gpu' in the parameter keys is a strong indicator.
        # This is a heuristic as the Ollama API doesn't give a simple 'device' field.
        if any('gpu' in key for key in details.get('parameters', {})):
            return "GPU"
        return "CPU"
    except Exception:
        # If the model isn't pulled or Ollama isn't running, we can't know.
        return "Unknown"

def run_ai_analysis(english_text, worker, screenshot_file, progress_bar):
    """
    Handles the OCR and Ollama analysis part of the workflow.
    """
    st.markdown("---")
    st.subheader("Call & Evidence Analysis")

    # --- Screenshot OCR ---
    screenshot_text = None
    if screenshot_file:
        progress_bar.progress(70, text="Analyzing screenshot...")
        try:
            ocr_instance = get_ocr_model()
            if ocr_instance:
                screenshot_text = extract_text_from_image(ocr_instance, screenshot_file.getvalue())
                if screenshot_text:
                    with st.expander("Extracted Screenshot Text"):
                        st.text(screenshot_text)
                else:
                    st.warning("Could not extract any text from the uploaded screenshot.")
                
                # Unload OCR model to free VRAM before running the local LLM
                global ocr_model
                if ocr_model is not None:
                    del ocr_model
                    ocr_model = None
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    st.info("Unloaded OCR model to free VRAM.")
        except Exception as e:
            st.error(f"An error occurred during screenshot processing: {e}")
    # --- Ollama Analysis ---
    progress_bar.progress(80, text="Categorizing issue with local AI...")
    with st.container(border=True):
        text_model_device = get_ollama_device_info('phi3')
        st.caption(f"Local AI Model: `phi3` on **{text_model_device}** | OCR Engine: `EasyOCR`")

        category, fix = categorize_and_suggest_fix(english_text, worker, screenshot_text=screenshot_text, model_name=worker.model_name)
        if category != "Error":
            st.markdown("##### Issue Category")
            st.info(category)
            st.markdown("##### Suggested Next Step")
            st.success(fix)

st.set_page_config(page_title="Speech Analyser", layout="wide")

st.markdown("<h1>Speech Translation & Analyser</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.header("File Translation Controls")
    model_name = st.selectbox("Whisper model", ["base", "small", "medium"], index=1)

    if st.button("Clear GPU cache", use_container_width=True):
        torch.cuda.empty_cache()
        st.success("GPU cache cleared.")

    if st.button("Clear logs", use_container_width=True):
        worker = get_worker()
        with worker.lock:
            worker._logs.clear()
        st.success("Logs cleared.")

device_name = "GPU" if torch.cuda.is_available() else "CPU"
gpu_memory_info = ""
if device_name == "GPU":
    total_gpu_memory_bytes = torch.cuda.get_device_properties(0).total_memory
    total_gpu_memory_gb = total_gpu_memory_bytes / (1024**3)
    gpu_memory_info = f" ({total_gpu_memory_gb:.2f} GB)"
st.caption(f"Device: **{device_name}{gpu_memory_info}** | Model: **{model_name}**")

st.markdown("---")

# --- Step 1: File Upload ---
st.subheader("Step 1: Upload Audio and Evidence")
col_audio, col_screenshot = st.columns(2)
with col_audio:
    uploaded_file = st.file_uploader("Upload an audio file for analysis", type=["wav", "mp3", "m4a"])
with col_screenshot:
    screenshot_file = st.file_uploader("Upload supplementary screenshot (optional)", type=["png", "jpg", "jpeg"])

start_analysis = st.button("Start Analysis", type="primary", use_container_width=True, disabled=not uploaded_file)

st.markdown("---")

# --- Step 2: Analysis Results ---
if start_analysis and uploaded_file:
    st.subheader("Step 2: Analysis Results")
    progress_bar = st.progress(0, text="Starting analysis...")

    try:
        # --- Model Loading ---
        progress_bar.progress(5, text="Loading Whisper model...")
        worker = get_worker()
        # Ensure the model is loaded, especially if it was unloaded in a previous run
        device = "cuda" if torch.cuda.is_available() else "cpu"
        if worker.model is None or worker.model_name != model_name:
            worker.load_model(model_name, device)

        # --- File Handling ---
        progress_bar.progress(10, text="Preparing audio file...")
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_audio:
            tmp_audio.write(uploaded_file.getvalue())
            tmp_audio_path = tmp_audio.name

        start_time = time.time()
        # --- Transcription ---
        progress_bar.progress(25, text="Transcribing audio to Tamil...")
        tamil_result = transcribe_robust(
            worker.model,
            tmp_audio_path,
            task="transcribe",
            language=SOURCE_LANGUAGE,
            fp16=True, temperature=0, condition_on_previous_text=False,
            no_speech_threshold=0.6, beam_size=5,
        )
        tamil_text = tamil_result.get("text", "").strip()

        # --- Translation ---
        progress_bar.progress(50, text="Translating text to English...")
        english_result = transcribe_robust(
            worker.model,
            tmp_audio_path,
            task="translate",
            language=SOURCE_LANGUAGE,
            fp16=True, temperature=0, condition_on_previous_text=False,
            no_speech_threshold=0.6, beam_size=5,
        )
        english_text = english_result.get("text", "").strip()
        end_time = time.time()
        translation_time = end_time - start_time

        # --- Display Transcription & Translation ---
        progress_bar.progress(60, text="Processing results...")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Tamil Transcription")
            st.text_area("Tamil", tamil_text, height=200)
        with col2:
            st.subheader("English Translation")
            st.text_area("English", english_text, height=200)
        st.caption(f"Transcription & Translation time: {translation_time:.2f} seconds")

        # --- AI Analysis Section ---
        if english_text and OLLAMA_AVAILABLE:
            run_ai_analysis(english_text, worker, screenshot_file, progress_bar)
        elif english_text:
            st.markdown("---")
            st.warning("The `ollama` or `easyocr` library is not installed, so call analysis is disabled.")
            st.code("pip install ollama easyocr", language="bash")
            st.info("Install the library and restart the app to enable this feature.")

        progress_bar.progress(100, text="Analysis complete!")
        time.sleep(1) # Give user a moment to see the final message
        progress_bar.empty() # Hide the progress bar

    except Exception as e:
        st.error(f"An error occurred: {e}")
        if 'progress_bar' in locals():
            progress_bar.empty()
