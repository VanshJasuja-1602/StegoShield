import io
import pytest
from PIL import Image
from capacity import calculate_image_capacity, validate_capacity_before_encoding, CapacityError

def create_sample_png(width=100, height=100) -> bytes:
    img = Image.new("RGB", (width, height), (100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def test_capacity_small_payload():
    """1. Test small payload capacity calculation."""
    png_bytes = create_sample_png(100, 100)
    msg = "Small secret payload"

    cap = calculate_image_capacity(png_bytes, msg, lsb_bits=1)

    assert cap["width"] == 100
    assert cap["height"] == 100
    assert cap["num_channels"] == 3
    assert cap["total_pixels"] == 10000
    assert cap["total_capacity_bytes"] == 3750  # 10000 * 3 / 8
    assert cap["message_size_bytes"] == len(msg)
    assert cap["used_capacity_bytes"] == cap["message_size_bytes"] + 52
    assert cap["remaining_capacity_bytes"] == 3750 - cap["used_capacity_bytes"]
    assert cap["is_exceeded"] is False

    # Validate before encoding passes
    val = validate_capacity_before_encoding(png_bytes, msg, lsb_bits=1)
    assert val["is_exceeded"] is False

def test_capacity_medium_payload():
    """2. Test medium payload capacity calculation."""
    png_bytes = create_sample_png(200, 200)  # 200x200x3 / 8 = 15,000 bytes capacity
    msg = "A" * 5000

    cap = calculate_image_capacity(png_bytes, msg, lsb_bits=1)

    assert cap["total_capacity_bytes"] == 15000
    assert cap["message_size_bytes"] == 5000
    assert cap["used_capacity_bytes"] == 5052
    assert cap["remaining_capacity_bytes"] == 9948
    assert cap["used_percentage"] < 50.0
    assert cap["is_exceeded"] is False

def test_capacity_oversized_payload_raises_error():
    """3. Test oversized payload triggers clear CapacityError before encoding."""
    png_bytes = create_sample_png(20, 20)  # 20x20x3 / 8 = 150 bytes capacity
    huge_msg = "X" * 500

    cap = calculate_image_capacity(png_bytes, huge_msg, lsb_bits=1)

    assert cap["total_capacity_bytes"] == 150
    assert cap["used_capacity_bytes"] == 552
    assert cap["remaining_capacity_bytes"] == 0
    assert cap["is_exceeded"] is True

    with pytest.raises(CapacityError) as exc_info:
        validate_capacity_before_encoding(png_bytes, huge_msg, lsb_bits=1)

    assert "Payload Exceeded Image Capacity" in str(exc_info.value)
