import streamlit as st

st.set_page_config(
    page_title="ISP Analysers",
    page_icon="👋",
    layout="wide"
)

st.title("Welcome to the ISP Analysers App 👋")

st.markdown(
    """
    This application provides tools for analyzing ISP data.
    You can use the various features from the sidebar to get started.
    """
)

st.header("Features")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🎤 Audio Analysis")
    st.write(
        "Upload audio files (WAV, MP3, M4A) to get a full transcription. "
        "The extracted text can then be analyzed to categorize customer issues."
    )

with col2:
    st.subheader("️ Screenshot Analysis")
    st.write(
        "Upload a supplementary screenshot (e.g., for payment or router errors). "
        "The tool uses OCR to extract text, which is then analyzed by the local AI model."
    )

st.info("Please select a page from the sidebar to get started.")

st.markdown(
    """
    ---
    **Powered by Ollama, Whisper, and Streamlit**
    """
)
