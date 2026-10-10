import io
from PIL import Image

class CapacityError(Exception):
    """Custom exception for capacity calculation and overflow errors."""
    pass

HEADER_OVERHEAD_BYTES = 52  # 4B magic + 4B length + 16B salt + 12B nonce + 16B tag

def calculate_image_capacity(
    image_input: bytes | str | Image.Image,
    message_text: str | bytes = "",
    lsb_bits: int = 1
) -> dict:
    """
    Calculate detailed image capacity metrics for a given PNG image and secret message.
    
    Returns dictionary with:
    - width
    - height
    - num_channels (3 for RGB)
    - total_pixels
    - total_lsb_capacity_bits
    - total_capacity_bytes
    - header_overhead_bytes
    - max_usable_payload_bytes / usable_payload_bytes
    - message_size_bytes
    - encrypted_payload_size_bytes
    - used_capacity_bytes
    - remaining_capacity_bytes
    - used_percentage
    - is_exceeded
    """
    if lsb_bits not in (1, 2):
        raise CapacityError("LSB bits per channel must be 1 or 2.")

    try:
        if isinstance(image_input, (bytes, bytearray)):
            img = Image.open(io.BytesIO(image_input))
        elif isinstance(image_input, str):
            img = Image.open(image_input)
        elif isinstance(image_input, Image.Image):
            img = image_input
        else:
            raise CapacityError("Unsupported image input type.")

        if img.format and img.format.upper() not in ("PNG", "BMP", "PPM"):
            if img.format.upper() == "JPEG":
                raise CapacityError("JPEG is a lossy format and unsupported. Only PNG images are supported.")
            raise CapacityError(f"Unsupported format: '{img.format}'. Only PNG images are supported.")

        img_rgb = img.convert("RGB")
    except CapacityError:
        raise
    except Exception as e:
        raise CapacityError(f"Failed to open image for capacity calculation: {str(e)}")

    width, height = img_rgb.size
    num_channels = 3  # RGB channels
    total_pixels = width * height
    total_lsb_capacity_bits = total_pixels * num_channels * lsb_bits
    total_capacity_bytes = total_lsb_capacity_bits // 8

    header_overhead = HEADER_OVERHEAD_BYTES
    max_usable_payload_bytes = max(0, total_capacity_bytes - header_overhead)

    if isinstance(message_text, str):
        message_size_bytes = len(message_text.encode('utf-8'))
    elif isinstance(message_text, (bytes, bytearray)):
        message_size_bytes = len(message_text)
    else:
        message_size_bytes = 0

    # Encryption overhead: 16B salt + 12B nonce + 16B tag = 44 bytes added to message
    encrypted_payload_size_bytes = message_size_bytes + 44 if message_size_bytes > 0 else 0

    # Total bytes embedded into pixels = 8 bytes stego header + encrypted payload size
    used_capacity_bytes = (HEADER_OVERHEAD_BYTES + message_size_bytes) if message_size_bytes > 0 else 0
    remaining_capacity_bytes = max(0, total_capacity_bytes - used_capacity_bytes)

    used_percentage = round((used_capacity_bytes / max(1, total_capacity_bytes)) * 100, 2)
    is_exceeded = used_capacity_bytes > total_capacity_bytes

    return {
        "width": width,
        "height": height,
        "num_channels": num_channels,
        "total_pixels": total_pixels,
        "lsb_bits": lsb_bits,
        "total_capacity_bytes": total_capacity_bytes,
        "header_overhead_bytes": header_overhead,
        "max_usable_payload_bytes": max_usable_payload_bytes,
        "usable_payload_bytes": max_usable_payload_bytes,
        "message_size_bytes": message_size_bytes,
        "encrypted_payload_size_bytes": encrypted_payload_size_bytes,
        "used_capacity_bytes": used_capacity_bytes,
        "remaining_capacity_bytes": remaining_capacity_bytes,
        "used_percentage": used_percentage,
        "is_exceeded": is_exceeded,
    }

def validate_capacity_before_encoding(
    image_input: bytes | str | Image.Image,
    message_text: str | bytes,
    lsb_bits: int = 1
) -> dict:
    """
    Validate that payload does not exceed cover image capacity before encoding.
    Raises CapacityError if payload is oversized.
    """
    cap = calculate_image_capacity(image_input, message_text, lsb_bits=lsb_bits)
    if cap["is_exceeded"]:
        raise CapacityError(
            f"Payload Exceeded Image Capacity: Message requires {cap['used_capacity_bytes']} bytes "
            f"(including overhead), but cover image maximum capacity is {cap['total_capacity_bytes']} bytes. "
            f"Please upload a larger PNG image or shorten your message."
        )
    return cap
