import io
import pytest
from PIL import Image
from steganography import encode_secret_with_password
from tamper_detection import (
    verify_stego_integrity,
    simulate_image_manipulation,
    STATUS_UNMODIFIED,
    STATUS_TAMPERED,
    STATUS_FAILED,
)

def create_sample_png(width=150, height=150) -> bytes:
    img = Image.new("RGB", (width, height), (120, 140, 160))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

@pytest.fixture
def stego_data():
    cover_png = create_sample_png(150, 150)
    secret_text = "StegoShield Integrity Verification Test Secret!"
    password = "IntegrityMasterPassword2026"
    stego_png = encode_secret_with_password(cover_png, secret_text, password, lsb_bits=1)
    return {
        "cover_png": cover_png,
        "stego_png": stego_png,
        "secret_text": secret_text,
        "password": password,
    }

def test_1_original_stego_image(stego_data):
    """1. Test original unmodified stego image yields 'Likely Unmodified'."""
    res = verify_stego_integrity(stego_data["stego_png"], stego_data["password"])

    assert res["status"] == STATUS_UNMODIFIED
    assert res["is_authentic"] is True
    assert res["decrypted_message"] == stego_data["secret_text"]

def test_2_modified_pixel(stego_data):
    """2. Test modified pixel yields 'Possible Tampering' due to AEAD MAC failure."""
    tampered_png = simulate_image_manipulation(stego_data["stego_png"], "modify_pixel")
    res = verify_stego_integrity(tampered_png, stego_data["password"])

    assert res["status"] in (STATUS_TAMPERED, STATUS_FAILED)
    assert res["is_authentic"] is False
    assert res["decrypted_message"] is None

def test_3_resized_image(stego_data):
    """3. Test resized image yields extraction failure/tampered status."""
    resized_png = simulate_image_manipulation(stego_data["stego_png"], "resize")
    res = verify_stego_integrity(resized_png, stego_data["password"])

    assert res["status"] in (STATUS_TAMPERED, STATUS_FAILED)
    assert res["is_authentic"] is False

def test_4_cropped_image(stego_data):
    """4. Test cropped image yields extraction failure status."""
    cropped_png = simulate_image_manipulation(stego_data["stego_png"], "crop")
    res = verify_stego_integrity(cropped_png, stego_data["password"])

    assert res["status"] in (STATUS_TAMPERED, STATUS_FAILED)
    assert res["is_authentic"] is False

def test_5_filtered_image(stego_data):
    """5. Test Gaussian blur filtered image yields tampering status."""
    filtered_png = simulate_image_manipulation(stego_data["stego_png"], "filter")
    res = verify_stego_integrity(filtered_png, stego_data["password"])

    assert res["status"] in (STATUS_TAMPERED, STATUS_FAILED)
    assert res["is_authentic"] is False

def test_6_recompressed_image(stego_data):
    """6. Test lossy JPEG recompressed image yields tampering status."""
    recompressed_png = simulate_image_manipulation(stego_data["stego_png"], "recompress")
    res = verify_stego_integrity(recompressed_png, stego_data["password"])

    assert res["status"] in (STATUS_TAMPERED, STATUS_FAILED)
    assert res["is_authentic"] is False
