"""Streamlit chat-style UI for live Tamil speech to English translation.

Run:
    C:/Users/aruna/anaconda3/python.exe -m streamlit run c:/arunaj/rough_book/streamlit_app.py

Architecture:
    Audio arrives from WebRTC → pushed onto an audio_queue.
    A persistent background thread reads from that queue, decodes with Whisper,
    and writes results to a thread-safe result_store.
    The Streamlit UI refreshes on a timer, reads from result_store, and renders chat.
    Streamlit reruns NEVER interrupt Whisper decode.
"""

import queue
import torch
import streamlit as st
from streamlit_webrtc import WebRtcMode, webrtc_streamer
from streamlit_webrtc.component import generate_frontend_component_key

from utils import get_worker, SAMPLE_RATE, DEFAULT_WINDOW_S, DEFAULT_STEP_S

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    def st_autorefresh(*args, **kwargs):
        return None


# ─── Session state defaults ───────────────────────────────────────────────────
def ensure_state():
    for k, v in {
        "messages": [],
        "last_tamil": "",
        "last_english": "",
        "last_stream_state": None,
        "last_selected_device": "",
    }.items():
        if k not in st.session_state:
            st.session_state[k] = v


def extract_selected_device(payload) -> str:
    if not isinstance(payload, dict):
        return ""
    for key in ("selectedAudioDeviceLabel", "selectedAudioInputDeviceLabel",
                "selectedDeviceLabel", "selectedDevice", "deviceLabel"):
        val = payload.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()
    audio = payload.get("audio")
    if isinstance(audio, dict):
        for key in ("deviceLabel", "label"):
            val = audio.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    return ""


# ─────────────────────────────────────────────────────────────────────────────
# Streamlit App
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Tamil Live Translator", layout="wide")
st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at 20% 20%, #e9f5ff 0%, #f8fbff 40%, #fffaf2 100%);
}
</style>
""", unsafe_allow_html=True)

ensure_state()

if not torch.cuda.is_available():
    st.error("GPU is required. Launch with: "
             "C:/Users/aruna/anaconda3/python.exe -m streamlit run streamlit_app.py")
    st.stop()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Session Controls")
    model_name = st.selectbox("Whisper model", ["base", "small", "medium"], index=1)
    window_seconds = st.slider("Context window (s)", 2.0, 10.0, DEFAULT_WINDOW_S, 0.5)
    step_seconds = st.slider("Decode every (s)", 0.5, 5.0, DEFAULT_STEP_S, 0.5)
    st.markdown("---")
    st.caption("Tamil → English translation.")

    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.last_tamil = ""
        st.session_state.last_english = ""

    if st.button("Clear GPU cache", use_container_width=True):
        torch.cuda.empty_cache()
        st.success("GPU cache cleared.")

    if st.button("Clear logs", use_container_width=True):
        worker = get_worker()
        with worker.lock:
            worker._logs.clear()

# ── Worker: load model & apply config ─────────────────────────────────────────
worker = get_worker()
worker.load_model(model_name, "cuda")
worker.window_samples = int(SAMPLE_RATE * window_seconds)
worker.step_seconds   = step_seconds

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("<h1>Tamil Live Translation Chat</h1>", unsafe_allow_html=True)
device_name = "GPU" if torch.cuda.is_available() else "CPU"
st.caption(f"Device: **{device_name}** | Model: **{model_name}**")

# ── Stats bar ─────────────────────────────────────────────────────────────────
stats = worker.get_stats()
c1, c2, c3 = st.columns(3)
c1.metric("Frames received", stats["frames_received"])
c2.metric("Chunks decoded",  stats["chunks_decoded"])
c3.metric("Last RMS",        f"{stats['last_rms']:.4f}")
c4, c5 = st.columns(2)
c4.metric("Buffer samples",  stats["buffer_samples"])
c5.metric("Last peak",       f"{stats['last_peak']:.4f}")
if stats["last_error"]:
    st.error(f"Last decode error: {stats['last_error']}")

# ── Processing log ─────────────────────────────────────────────────────────────
with st.expander("Processing log", expanded=False):
    logs = worker.get_logs()
    st.code("\n".join(logs[-80:]) if logs else "(no logs yet)", language="text")

# ── WebRTC streamer ───────────────────────────────────────────────────────────


ctx = webrtc_streamer(
    key="tamil-live-chat",
    mode=WebRtcMode.SENDONLY,
    media_stream_constraints={"video": False, "audio": True},
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    audio_receiver_size=AUDIO_RECEIVER_SIZE,
    translations={"select_device": "Selected device"},
    async_processing=True,
)

# Device label
frontend_key = generate_frontend_component_key("tamil-live-chat")
selected_device = extract_selected_device(st.session_state.get(frontend_key) or {})
if selected_device:
    st.caption(f"Selected device: {selected_device}")
    if selected_device != st.session_state.last_selected_device:
        worker._log(f"Device: {selected_device}")
        st.session_state.last_selected_device = selected_device
else:
    st.caption("Selected device: Browser-selected microphone")

# Stream status
is_streaming = bool(ctx.state.playing)
if is_streaming:
    st_autorefresh(interval=2000, key="audio-refresh")
    st.success("Microphone active — speak in Tamil.")
    if st.session_state.last_stream_state is not True:
        worker._log("Streaming started.")
        st.session_state.last_stream_state = True
else:
    st.warning("Click START to begin live translation.")
    if st.session_state.last_stream_state is not False:
        worker._log("Streaming stopped.")
        st.session_state.last_stream_state = False

# ── Feed audio to worker ──────────────────────────────────────────────────────
if is_streaming and ctx.audio_receiver:
    frames = []
    while len(frames) < 256:
        try:
            batch = ctx.audio_receiver.get_frames(timeout=0.02 if not frames else 0)
            if not batch:
                break
            frames.extend(batch)
        except queue.Empty:
            break
    if frames:
        worker.push_frames(frames)

# ── Pull decode results into session messages ─────────────────────────────────
def _remove_overlap(prev: str, curr: str) -> str:
    pw, cw = prev.split(), curr.split()
    for size in range(min(len(pw), len(cw)), 0, -1):
        if pw[-size:] == cw[:size]:
            return " ".join(cw[size:]).strip()
    return curr

for result in worker.pop_new_results():
    tamil_show   = _remove_overlap(st.session_state.last_tamil,   result["tamil"])   or result["tamil"]
    english_show = _remove_overlap(st.session_state.last_english, result["english"]) or result["english"]

    if tamil_show or english_show:
        st.session_state.messages.append({
            "timestamp": result["timestamp"],
            "tamil":     tamil_show,
            "english":   english_show,
        })
    if result["tamil"]:
        st.session_state.last_tamil = result["tamil"]
    if result["english"]:
        st.session_state.last_english = result["english"]

# ── Chat output ────────────────────────────────────────────────────────────────
if not st.session_state.messages:
    st.info(
        "**Welcome!** This app translates live Tamil speech to English.\\n\\n"
        "When you speak, you will see the original **Tamil** script and the final **English** translation.\\n\\n"
        "Click START and speak into your microphone. Translations will appear here."
    )

for msg in st.session_state.messages:
    with st.chat_message("user"):
        st.markdown(f"**Tamil ({msg['timestamp']}):** {msg['tamil']}")

    with st.chat_message("assistant"):
        st.markdown(f"**English:** {msg['english']}")
