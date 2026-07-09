import whisper
import sys

# Pre-download and cache Whisper models to avoid download on first use.
print("› Pre-caching Whisper models...")
try:
    for model_name in ["base", "small", "medium"]:
        print(f"  - Caching '{model_name}' model...")
        whisper.load_model(model_name)
    print("› All Whisper models cached successfully.")
except Exception as e:
    print(f"  - Error caching models: {e}", file=sys.stderr)
    print("  - The application will still attempt to download them on first use.", file=sys.stderr)
    # Exit with a non-zero code to indicate a non-critical failure if needed,
    # but for now, we'll let the main script continue.
    pass