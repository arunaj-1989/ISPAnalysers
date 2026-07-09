import streamlit as st
import whisper
import torch
import tempfile
import time
from utils import get_worker, SOURCE_LANGUAGE
import re
from pathlib import Path

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

def analyze_payment_screenshot(image_bytes: bytes) -> str:
    """
    Uses a vision model via Ollama to perform OCR on a payment screenshot.
    """
    # In a real app, you'd get this dynamically, e.g., from datetime.now()
    current_month_year = time.strftime("%B %Y")

    prompt = f"""
    You are an expert OCR assistant for Interjet ISP. Your task is to analyze the provided image of a payment receipt and extract key details.

    Refer to the "Payment Screenshot Analysis" section of the company's SOPs for the information you need to find:
    - Transaction ID / Reference Number.
    - Date and Time of payment.
    - Amount Paid.
    - Beneficiary Name (should be "Interjet" or similar).

    After extracting the information, please check if the 'Date of Payment' falls within the current month and year ({current_month_year}).

    Provide your response as a concise summary.
    """

    try:
        with st.spinner("Analyzing payment screenshot..."):
            response = ollama.chat(
                model='llava-phi3', # Use the vision model
                messages=[
                    {
                        'role': 'user',
                        'content': prompt,
                        'images': [image_bytes], # Pass the image bytes
                    },
                ],
            )
            return response['message']['content']
    except Exception as e:
        st.error(f"Could not connect to the Ollama vision model. Please ensure you have run `ollama pull llava-phi3`.")
        return f"An error occurred during image analysis: {e}"

def categorize_and_suggest_fix(translated_text: str, worker) -> (str, str):
    """
    Uses an Ollama SLM to categorize the text and provide a suggested fix
    based on the skill.md file.
    """
    try:
        skill_content = Path("skill.md").read_text(encoding="utf-8")
        model_name = worker.model_name # Keep track of the current whisper model
    except FileNotFoundError:
        st.error("The `skill.md` file was not found. Please ensure it exists in the root directory.")
        return "Error", "The `skill.md` file was not found."

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

    Based on the SOPs and the conversation, please perform the following:
    1.  **Categorize the issue:** Choose the most appropriate category from the "Issue Categories" section of the SOPs.
    2.  **Suggest a fix:** Provide a clear, step-by-step fix based on the troubleshooting steps or procedures in the SOPs for the identified category.

    Provide your response in the following format, and nothing else:
    Category: [The category you identified]
    Fix: [The suggested fix]
    """

    try:
        # Unload Whisper model to free up VRAM for Ollama
        st.info("Unloading Whisper model to free up VRAM for local AI...")
        worker.model = None
        torch.cuda.empty_cache()
        time.sleep(2) # Give a moment for memory to be released

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
        st.info("Reloading Whisper model...")
        worker.load_model(model_name, "cuda")


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

uploaded_file = st.file_uploader("Upload an audio file", type=["wav", "mp3", "m4a"])

if uploaded_file is not None:
    with st.spinner("Translating..."):
        worker = get_worker()
        worker.load_model(model_name, "cuda")

        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp_audio:
            tmp_audio.write(uploaded_file.getvalue())
            tmp_audio_path = tmp_audio.name

        try:
            start_time = time.time()
            # Transcribe (Tamil)
            tamil_result = transcribe_robust(
                worker.model,
                tmp_audio_path,
                task="transcribe",
                language=SOURCE_LANGUAGE,
                fp16=True,
                temperature=0,
                condition_on_previous_text=False,
                no_speech_threshold=0.6,
                beam_size=5,
            )
            tamil_text = tamil_result.get("text", "").strip()

            # Translate (English)
            english_result = transcribe_robust(
                worker.model,
                tmp_audio_path,
                task="translate",
                language=SOURCE_LANGUAGE,
                fp16=True,
                temperature=0,
                condition_on_previous_text=False,
                no_speech_threshold=0.6,
                beam_size=5,
            )
            english_text = english_result.get("text", "").strip()
            end_time = time.time()
            translation_time = end_time - start_time

            st.markdown("---")
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Tamil Transcription")
                st.text_area("Tamil", tamil_text, height=200)

            with col2:
                st.subheader("English Translation")
                st.text_area("English", english_text, height=200)

            st.caption(f"Translation time: {translation_time:.2f} seconds")

            # --- Analysis Section ---
            if english_text:
                st.markdown("---")
                st.subheader("Call Analysis")
                if OLLAMA_AVAILABLE:
                    with st.container(border=True):
                        category, fix = categorize_and_suggest_fix(english_text, worker)
                        if category != "Error":
                            col3, col4 = st.columns(2)
                            with col3:
                                st.markdown("##### Issue Category")
                                st.info(category)

                            with col4:
                                st.markdown("##### Suggested Next Step")
                                st.success(fix)

                        # Add the payment verification section if relevant
                        if "billing" in category.lower() or "deactivated" in category.lower():
                            st.markdown("---")
                            st.markdown("##### Payment Verification")
                            screenshot_file = st.file_uploader("Upload Payment Screenshot", type=["png", "jpg", "jpeg"])
                            if screenshot_file:
                                analysis_result = analyze_payment_screenshot(screenshot_file.getvalue())
                                st.markdown("###### Analysis Result")
                                st.info(analysis_result)
                else:
                    st.warning("The `ollama` library is not installed, so call analysis is disabled.")
                    st.code("pip install ollama", language="bash")
                    st.info("Install the library and restart the app to enable this feature.")

        except Exception as e:
            st.error(f"An error occurred: {e}")
