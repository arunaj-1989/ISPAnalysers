import queue
import tempfile
import threading
import time
from pathlib import Path

import numpy as np
import streamlit as st
import torch
from scipy.io.wavfile import write as wav_write

try:
    import whisper
    if str(getattr(whisper, "__file__", "")).endswith("whisper.py"):
        raise ImportError("Detected legacy 'whisper' package.")
except Exception as exc:
    st.error(
        "Whisper import failed. Run: "
        "C:/Users/aruna/anaconda3/python.exe -m pip install openai-whisper"
    )
    st.caption(str(exc))
    st.stop()

# ─── Constants ───────────────────────────────────────────────────────────────
SOURCE_LANGUAGE: str | None = "ta"
SAMPLE_RATE         = 16000
AUDIO_RECEIVER_SIZE = 1024
TARGET_PEAK         = 0.9
MAX_LOG_LINES       = 300
DEFAULT_WINDOW_S    = 6.0
DEFAULT_STEP_S      = 2.0


# ─── Background decode worker ────────────────────────────────────────────────
class DecodeWorker:
    """Runs Whisper decode in a background thread, immune to Streamlit reruns."""

    def __init__(self):
        self.audio_queue: queue.Queue = queue.Queue(maxsize=200)
        self._result_store: list = []
        self._logs: list = []
        self.lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self._running = False
        self.model = None
        self.model_name = ""
        # Stats
        self.frames_received = 0
        self.chunks_decoded  = 0
        self.last_rms  = 0.0
        self.last_peak = 0.0
        self.last_error = ""
        self._buffer = np.empty((0,), dtype=np.float32)
        # Config (updated by UI on each rerun)
        self.window_samples = int(SAMPLE_RATE * DEFAULT_WINDOW_S)
        self.step_seconds   = DEFAULT_STEP_S
        self.min_rms        = 0.0001

    # ── Model loading ────────────────────────────────────────────────────────
    def load_model(self, model_name: str, device: str):
        if self.model_name == model_name:
            return
        self._log(f"Loading Whisper '{model_name}' on {device}…")
        self.model = whisper.load_model(model_name, device=device)
        self.model_name = model_name
        self._log(f"Model '{model_name}' ready.")

    # ── Start / stop ─────────────────────────────────────────────────────────
    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self._log("Decode worker started.")

    def stop(self):
        self._running = False

    # ── API for Streamlit rerun ───────────────────────────────────────────────
    def push_frames(self, frames):
        with self.lock:
            self.frames_received += len(frames)
        for frame in frames:
            mono = self._pcm_to_mono(frame.to_ndarray())
            try:
                self.audio_queue.put_nowait(mono)
            except queue.Full:
                pass  # drop silently; old audio is less useful anyway

    def pop_new_results(self) -> list:
        with self.lock:
            out = list(self._result_store)
            self._result_store.clear()
            return out

    def get_logs(self) -> list:
        with self.lock:
            return list(self._logs)

    def get_stats(self) -> dict:
        with self.lock:
            return {
                "frames_received": self.frames_received,
                "chunks_decoded":  self.chunks_decoded,
                "last_rms":        self.last_rms,
                "last_peak":       self.last_peak,
                "last_error":      self.last_error,
                "buffer_samples":  len(self._buffer),
            }

    # ── Internal loop (background thread) ────────────────────────────────────
    def _loop(self):
        last_decode_ts = 0.0
        while self._running:
            # Drain all queued audio into buffer
            got_audio = False
            while True:
                try:
                    chunk = self.audio_queue.get(timeout=0.05)
                    self._buffer = np.concatenate((self._buffer, chunk))
                    got_audio = True
                except queue.Empty:
                    break

            if not got_audio:
                time.sleep(0.05)
                continue

            # Trim old audio
            max_buf = self.window_samples * 4
            if len(self._buffer) > max_buf:
                self._buffer = self._buffer[-max_buf:]

            # Decode on cadence once buffer has enough audio
            now = time.time()
            min_buf = int(SAMPLE_RATE * 1.5)
            if len(self._buffer) >= min_buf and (now - last_decode_ts) >= self.step_seconds:
                last_decode_ts = now
                self._decode(self._buffer[-self.window_samples:])

    def _decode(self, chunk: np.ndarray):
        if self.model is None:
            return

        rms  = float(np.sqrt(np.mean(np.square(chunk))))
        peak = float(np.max(np.abs(chunk))) if chunk.size else 0.0
        with self.lock:
            self.last_rms  = rms
            self.last_peak = peak

        # Auto-gain quiet input
        chunk_out = chunk.copy()
        if peak > 0:
            chunk_out = np.clip(chunk_out * min(60.0, TARGET_PEAK / peak), -1.0, 1.0)

        chunk_int16 = np.int16(chunk_out * 32767)
        tmp = Path(tempfile.mktemp(suffix=".wav"))
        try:
            wav_write(str(tmp), SAMPLE_RATE, chunk_int16)
            self._log(f"Decoding – rms={rms:.4f}  peak={peak:.4f}  samples={len(chunk)}")

            tamil_r = self.model.transcribe(
                str(tmp), task="transcribe", language=SOURCE_LANGUAGE,
                fp16=True, temperature=0, condition_on_previous_text=False,
                no_speech_threshold=0.6, beam_size=5,
            )
            self._log("Tamil done.")

            english_r = self.model.transcribe(
                str(tmp), task="translate", language=SOURCE_LANGUAGE,
                fp16=True, temperature=0, condition_on_previous_text=False,
                no_speech_threshold=0.6, beam_size=5,
            )
            self._log("English done.")

            with self.lock:
                self.chunks_decoded += 1
                self.last_error = ""

            tamil   = " ".join((tamil_r.get("text",   "") or "").strip().split())
            english = " ".join((english_r.get("text", "") or "").strip().split())

            self._log(f"T: {tamil[:80]!r}")
            self._log(f"E: {english[:80]!r}")

            if tamil or english:
                with self.lock:
                    self._result_store.append({
                        "timestamp": time.strftime("%H:%M:%S"),
                        "tamil":     tamil,
                        "english":   english,
                    })

        except Exception as exc:
            with self.lock:
                self.last_error = str(exc)
            self._log(f"Error: {exc}")
        finally:
            tmp.unlink(missing_ok=True)

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _log(self, msg: str):
        ts = time.strftime("%H:%M:%S")
        with self.lock:
            self._logs.append(f"[{ts}] {msg}")
            if len(self._logs) > MAX_LOG_LINES:
                self._logs = self._logs[-MAX_LOG_LINES:]

    @staticmethod
    def _pcm_to_mono(pcm: np.ndarray) -> np.ndarray:
        if pcm.ndim == 2:
            pcm = (pcm.mean(axis=0) if pcm.shape[0] <= 2 and pcm.shape[0] < pcm.shape[1]
                   else pcm.mean(axis=1))
        if np.issubdtype(pcm.dtype, np.integer):
            pcm = pcm.astype(np.float32) / float(np.iinfo(pcm.dtype).max)
        else:
            pcm = pcm.astype(np.float32)
            if pcm.size and float(np.max(np.abs(pcm))) > 1.5:
                pcm = pcm / 32768.0
        return np.clip(pcm, -1.0, 1.0)


# ─── Single shared worker (survives Streamlit reruns) ────────────────────────
@st.cache_resource(show_spinner=False)
def get_worker() -> DecodeWorker:
    w = DecodeWorker()
    w.start()
    return w
