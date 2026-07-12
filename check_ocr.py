import sys
import logging

def try_init(easyocr, torch, device="cpu"):
    """Attempts to initialize PaddleOCR on the given device."""
    try:
        use_gpu = device == "gpu" and torch.cuda.is_available()
        _ = easyocr.Reader(['en'], gpu=use_gpu)
        print(f"  - ✅ SUCCESS: EasyOCR initialized in {device.upper()} mode successfully!")
        return True
    except Exception as e:
        print(f"  - ❌ FAILURE: Could not initialize EasyOCR in {device.upper()} mode.")
        print(f"    - Error details: {e}")
        return False

def run_ocr_check():
    """Performs a diagnostic check on the EasyOCR installation."""
    print("\n=====================================")
    print("   EasyOCR Installation Checker")
    print("=====================================")

    try:
        import torch
        import easyocr

        # Suppress verbose logging from EasyOCR
        logging.getLogger('easyocr').setLevel(logging.ERROR)

        print("\n› Found 'torch' and 'easyocr' libraries.")
    except ImportError as e:
        print(f"\n❌ Critical Error: Failed to import a required library: {e}")
        print("   Please ensure you have run 'pip install -r requirements.txt' in your virtual environment.")
        return
    
    print("\n› Step 1: Checking PyTorch GPU support...")
    if torch.cuda.is_available():
        print("  - ✅ Your version of PyTorch supports GPU.")
        print("\n› Step 2: Testing GPU mode initialization...")
        if try_init(easyocr, torch, device="gpu"):
            return  # Success, no need to test CPU
    else:
        print("  - ⚠️ Your version of PyTorch is CPU-only or CUDA is not configured correctly.")
    
    print("\n› Final Step: Testing CPU mode...")
    try_init(easyocr, torch, device="cpu")

if __name__ == "__main__":
    run_ocr_check()
