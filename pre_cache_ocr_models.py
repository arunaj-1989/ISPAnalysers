import sys

try:
    import easyocr
    import torch

    print("› Pre-caching EasyOCR models...")

    # Check if CUDA is available
    use_gpu_for_ocr = torch.cuda.is_available()
    if use_gpu_for_ocr:
        print("  - GPU detected. Caching models for GPU execution.")
    else:
        print("  - GPU not detected. Caching models for CPU execution.")


    # Initializing EasyOCR with the required settings will trigger the download.
    # We only need to cache for one language.
    easyocr.Reader(['en'], gpu=use_gpu_for_ocr)
    print("› All EasyOCR models cached successfully.")
except Exception as e:
    print(f"  - Error caching EasyOCR models: {e}", file=sys.stderr)
    print("  - The application will still attempt to download them on first use.", file=sys.stderr)
    pass