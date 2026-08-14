import contextlib
import io

from app import suppress_library_output, infer_ollama_runtime_device


def test_suppress_library_output_blocks_terminal_noise():
    captured = io.StringIO()

    with contextlib.redirect_stdout(captured):
        with suppress_library_output():
            print("terminal progress noise")

    assert "terminal progress noise" not in captured.getvalue()


def test_infer_ollama_runtime_device_detects_gpu_from_ollama_ps():
    device = infer_ollama_runtime_device(
        "llama3:latest",
        show_result={"details": {"parameters": {}}},
        ps_result={"models": [{"name": "llama3:latest", "size_vram": 1024}]},
    )

    assert device == "GPU"


def test_infer_ollama_runtime_device_defaults_to_cpu_without_gpu_signal():
    device = infer_ollama_runtime_device(
        "llama3:latest",
        show_result={"details": {"parameters": {}}},
        ps_result={"models": [{"name": "llama3:latest", "size_vram": 0}]},
    )

    assert device == "CPU"
