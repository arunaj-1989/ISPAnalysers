import streamlit as st

st.set_page_config(
    page_title="Tamil Speech Translation",
    page_icon="👋",
    layout="wide"
)

st.title("Welcome to the Tamil Speech Translation App 👋")

st.markdown(
    """
    This application provides tools for translating Tamil speech into English.
    You can either translate live audio from your microphone or upload an audio file for translation.
    """
)

st.header("Features")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🎤 Live Speech Translation")
    st.write(
        "Navigate to the **Streaming Audio** page from the sidebar to start translating live audio from your microphone. "
        "This feature is ideal for real-time translation during conversations."
    )

with col2:
    st.subheader("📂 Audio File Translation")
    st.write(
        "Navigate to the **1_File_Translation** page (will be displayed as 'File Translation' in the sidebar) "
        "to upload an audio file (WAV, MP3, M4A) and get the Tamil transcription and English translation. "
        "This is useful for translating pre-recorded audio."
    )

st.info("Please select a page from the sidebar to get started.")

st.markdown(
    """
    ---
    **Powered by Whisper**
    """
)
