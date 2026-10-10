"""
StegoShield Tamper Detection & Integrity Verification Module.

IMPORTANT LIMITATIONS OF LSB STEGANOGRAPHY INTEGRITY DETECTION:
1. Spatial LSB steganography relies on exact pixel bit preservation.
2. Lossy operations (JPEG recompression, Gaussian filtering, spatial resizing, cropping)
   destroy or shift fragile LSB bitplanes.
3. Cryptographic AEAD (AES-256-GCM) authentication tags guarantee that modified payloads
   will be detected as 'Possible Tampering' or 'Corrupted / Extraction Failed', but original
   payload data CANNOT be recovered after lossy image alterations.
"""

import io
from PIL import Image, ImageFilter
import numpy as np
from encryption import decrypt_message, EncryptionError
from steganography import decode_message, SteganographyError

class TamperDetectionError(Exception):
    """Custom exception for tamper detection failures."""
    pass

LIMITATIONS_NOTICE = (
    "Note on Steganographic Limitations: Spatial LSB embedding is fragile against lossy "
    "image transformations (such as JPEG recompression, cropping, resizing, or blur filtering). "
    "While StegoShield's AES-256-GCM authentication reliably detects bit tampering and payload corruption, "
    "destroyed pixel bits cannot be mathematically recovered."
)

STATUS_UNMODIFIED = "Likely Unmodified"
STATUS_TAMPERED = "Possible Tampering"
STATUS_FAILED = "Corrupted / Extraction Failed"

def verify_stego_integrity(stego_image_input: bytes | str | Image.Image, password: str) -> dict:
    """
    Verify the integrity of a stego PNG image and extract payload if valid.
    
    Returns structured dict:
    - status: "Likely Unmodified" | "Possible Tampering" | "Corrupted / Extraction Failed"
    - status_code: "UNMODIFIED" | "TAMPERED" | "FAILED"
    - is_authentic: bool
    - decrypted_message: str or None
    - error_details: str or None
    - limitations_notice: str
    """
    if not password:
        return {
            "status": STATUS_FAILED,
            "status_code": "FAILED",
            "is_authentic": False,
            "decrypted_message": None,
            "error_details": "Password is required for integrity verification.",
            "limitations_notice": LIMITATIONS_NOTICE,
        }

    # Step 1: Attempt LSB payload extraction & magic header check
    try:
        extracted_payload = decode_message(stego_image_input, lsb_bits=1)
    except SteganographyError as stego_err:
        err_msg = str(stego_err)
        if "Header check failed" in err_msg or "too small" in err_msg:
            return {
                "status": STATUS_FAILED,
                "status_code": "FAILED",
                "is_authentic": False,
                "decrypted_message": None,
                "error_details": f"Header Validation Error: {err_msg}",
                "limitations_notice": LIMITATIONS_NOTICE,
            }
        else:
            return {
                "status": STATUS_TAMPERED,
                "status_code": "TAMPERED",
                "is_authentic": False,
                "decrypted_message": None,
                "error_details": f"Pixel Bit Corruption Detected: {err_msg}",
                "limitations_notice": LIMITATIONS_NOTICE,
            }

    # Step 2: Attempt AES-256-GCM AEAD decryption & MAC verification
    try:
        decrypted_message = decrypt_message(extracted_payload, password)
        return {
            "status": STATUS_UNMODIFIED,
            "status_code": "UNMODIFIED",
            "is_authentic": True,
            "decrypted_message": decrypted_message,
            "error_details": None,
            "limitations_notice": LIMITATIONS_NOTICE,
        }
    except EncryptionError as crypto_err:
        err_msg = str(crypto_err)
        if "Incorrect password" in err_msg or "corrupted payload" in err_msg:
            return {
                "status": STATUS_TAMPERED,
                "status_code": "TAMPERED",
                "is_authentic": False,
                "decrypted_message": None,
                "error_details": f"AEAD Authentication Tag Failure: {err_msg}",
                "limitations_notice": LIMITATIONS_NOTICE,
            }
        return {
            "status": STATUS_FAILED,
            "status_code": "FAILED",
            "is_authentic": False,
            "decrypted_message": None,
            "error_details": err_msg,
            "limitations_notice": LIMITATIONS_NOTICE,
        }

def simulate_image_manipulation(image_bytes: bytes, action: str) -> bytes:
    """
    Helper function to simulate image manipulation for tamper testing:
    - 'modify_pixel': Flips LSB bit in embedded payload pixel region.
    - 'resize': Resizes image by 50%.
    - 'crop': Crops image to top-left quadrant.
    - 'filter': Applies Gaussian Blur filter.
    - 'recompress': Saves image as lossy JPEG and re-converts to PNG.
    """
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    if action == "modify_pixel":
        px = np.array(img, dtype=np.uint8)
        px[0, 15, 0] ^= 1  # Flip LSB of payload pixel
        mod_img = Image.fromarray(px, mode="RGB")
        buf = io.BytesIO()
        mod_img.save(buf, format="PNG")
        return buf.getvalue()

    elif action == "resize":
        new_size = (max(10, img.width // 2), max(10, img.height // 2))
        resized_img = img.resize(new_size, Image.Resampling.BILINEAR)
        buf = io.BytesIO()
        resized_img.save(buf, format="PNG")
        return buf.getvalue()

    elif action == "crop":
        box = (0, 0, max(10, img.width // 2), max(10, img.height // 2))
        cropped_img = img.crop(box)
        buf = io.BytesIO()
        cropped_img.save(buf, format="PNG")
        return buf.getvalue()

    elif action == "filter":
        filtered_img = img.filter(ImageFilter.GaussianBlur(radius=1.5))
        buf = io.BytesIO()
        filtered_img.save(buf, format="PNG")
        return buf.getvalue()

    elif action == "recompress":
        jpeg_buf = io.BytesIO()
        img.save(jpeg_buf, format="JPEG", quality=80)
        jpeg_img = Image.open(io.BytesIO(jpeg_buf.getvalue())).convert("RGB")
        png_buf = io.BytesIO()
        jpeg_img.save(png_buf, format="PNG")
        return png_buf.getvalue()

    else:
        raise ValueError(f"Unknown manipulation action: {action}")
