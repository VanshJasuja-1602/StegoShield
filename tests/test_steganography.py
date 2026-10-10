import io
import pytest
from PIL import Image
from steganography import (
    calculate_capacity,
    encode_message,
    decode_message,
    encode_secret_with_password,
    decode_secret_with_password,
    SteganographyError,
)

def create_sample_png(width=100, height=100, color=(120, 140, 160)) -> bytes:
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def create_sample_jpeg(width=100, height=100) -> bytes:
    img = Image.new("RGB", (width, height), (120, 140, 160))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def test_calculate_capacity():
    png_bytes = create_sample_png(100, 100)
    cap = calculate_capacity(png_bytes, lsb_bits=1)
    
    # 100x100x3 = 30,000 bits = 3,750 bytes total capacity
    assert cap["width"] == 100
    assert cap["height"] == 100
    assert cap["total_capacity_bytes"] == 3750
    assert cap["metadata_overhead_bytes"] == 8
    assert cap["usable_payload_bytes"] == 3742

def test_small_payload():
    """1. Test small payload embedding and extraction."""
    cover_png = create_sample_png(50, 50)
    small_payload = b"Hello, StegoShield!"

    stego_png = encode_message(cover_png, small_payload, lsb_bits=1)
    extracted_payload = decode_message(stego_png, lsb_bits=1)

    assert extracted_payload == small_payload

def test_large_payload():
    """2. Test large payload embedding near image capacity limit."""
    cover_png = create_sample_png(200, 200) # 200x200x3 = 120,000 bits = 15,000 bytes capacity
    cap = calculate_capacity(cover_png, lsb_bits=1)
    
    large_payload = b"A" * (cap["usable_payload_bytes"] - 10)

    stego_png = encode_message(cover_png, large_payload, lsb_bits=1)
    extracted_payload = decode_message(stego_png, lsb_bits=1)

    assert extracted_payload == large_payload

def test_capacity_exceeded():
    """3. Test capacity exceeded raises SteganographyError."""
    cover_png = create_sample_png(20, 20)  # 20x20x3 = 1200 bits = 150 bytes capacity
    huge_payload = b"X" * 1000

    with pytest.raises(SteganographyError) as exc_info:
        encode_message(cover_png, huge_payload, lsb_bits=1)
    assert "exceeds usable image capacity" in str(exc_info.value)

def test_encode_decode_round_trip_with_password():
    """4. Test end-to-end encode/decode round trip with password."""
    cover_png = create_sample_png(120, 120)
    secret_text = "End-to-end encrypted secret message with password!"
    password = "MySecurePassword2026"

    stego_png = encode_secret_with_password(cover_png, secret_text, password, lsb_bits=1)
    recovered_text = decode_secret_with_password(stego_png, password, lsb_bits=1)

    assert recovered_text == secret_text

def test_non_stego_image_fails():
    """5. Test extracting from non-stego image fails header check."""
    normal_png = create_sample_png(100, 100)

    with pytest.raises(SteganographyError) as exc_info:
        decode_message(normal_png, lsb_bits=1)
    assert "Header check failed" in str(exc_info.value)

def test_corrupted_image():
    """6. Test corrupted stego image or invalid header length."""
    cover_png = create_sample_png(50, 50)
    payload = b"Sample payload"
    stego_png = bytearray(encode_message(cover_png, payload, lsb_bits=1))

    # Tamper magic marker header bytes
    stego_png[0] ^= 0xFF

    with pytest.raises(SteganographyError):
        decode_message(bytes(stego_png), lsb_bits=1)

def test_wrong_password_scenario():
    """7. Test extraction with wrong password fails safely."""
    cover_png = create_sample_png(100, 100)
    secret_text = "Highly Confidential Stego Payload"
    correct_pass = "CorrectPassword"
    wrong_pass = "WrongPassword"

    stego_png = encode_secret_with_password(cover_png, secret_text, correct_pass, lsb_bits=1)

    with pytest.raises(SteganographyError) as exc_info:
        decode_secret_with_password(stego_png, wrong_pass, lsb_bits=1)
    assert "Decryption failed" in str(exc_info.value)

def test_jpeg_image_rejection():
    """Test JPEG rejection requirement."""
    jpeg_bytes = create_sample_jpeg(100, 100)
    with pytest.raises(SteganographyError) as exc_info:
        encode_message(jpeg_bytes, b"test")
    assert "JPEG is a lossy format" in str(exc_info.value)
