import io
import struct
import numpy as np
from PIL import Image
from encryption import encrypt_message, decrypt_message, EncryptionError

class SteganographyError(Exception):
    """Custom exception for steganography errors."""
    pass

MAGIC_MARKER = b"STEG"
HEADER_SIZE = 8  # 4 bytes magic + 4 bytes length

def validate_png_image(image_input: bytes | str | Image.Image) -> Image.Image:
    """
    Validate that the input image is a valid PNG image and return a PIL Image object in RGB mode.
    Raises SteganographyError if format is not PNG or image is invalid.
    """
    try:
        if isinstance(image_input, (bytes, bytearray)):
            img = Image.open(io.BytesIO(image_input))
        elif isinstance(image_input, str):
            img = Image.open(image_input)
        elif isinstance(image_input, Image.Image):
            img = image_input
        else:
            raise SteganographyError("Unsupported image input type.")

        # Check image format if available (JPEG/WEBP rejection)
        if img.format and img.format.upper() not in ("PNG", "BMP", "PPM"):
            if img.format.upper() == "JPEG":
                raise SteganographyError("JPEG is a lossy format and destroys LSB steganography. Only PNG is supported.")
            raise SteganographyError(f"Unsupported image format: '{img.format}'. Only PNG images are supported.")

        return img.convert("RGB")
    except SteganographyError:
        raise
    except Exception as e:
        raise SteganographyError(f"Failed to load image: {str(e)}")

def calculate_capacity(image_input: bytes | str | Image.Image, lsb_bits: int = 1) -> dict:
    """
    Calculate the total and usable embedding capacity of a PNG image.
    
    Returns dict:
    - width
    - height
    - total_pixels
    - lsb_bits
    - total_capacity_bytes
    - metadata_overhead_bytes (8 bytes)
    - usable_payload_bytes
    """
    if lsb_bits not in (1, 2):
        raise SteganographyError("LSB bits per channel must be 1 or 2.")

    img = validate_png_image(image_input)
    width, height = img.size
    total_pixels = width * height
    total_channel_values = total_pixels * 3  # RGB channels
    total_bits = total_channel_values * lsb_bits
    total_capacity_bytes = total_bits // 8

    metadata_overhead = HEADER_SIZE
    usable_payload_bytes = max(0, total_capacity_bytes - metadata_overhead)

    return {
        "width": width,
        "height": height,
        "total_pixels": total_pixels,
        "lsb_bits": lsb_bits,
        "total_capacity_bytes": total_capacity_bytes,
        "metadata_overhead_bytes": metadata_overhead,
        "usable_payload_bytes": usable_payload_bytes,
    }

def encode_message(image_input: bytes | str | Image.Image, secret_payload: bytes, lsb_bits: int = 1) -> bytes:
    """
    Embed an encrypted binary payload into the RGB LSB bits of a PNG image.
    Returns resulting PNG image as bytes.
    """
    if not secret_payload or not isinstance(secret_payload, (bytes, bytearray)):
        raise SteganographyError("Secret payload cannot be empty.")

    if lsb_bits not in (1, 2):
        raise SteganographyError("LSB bits per channel must be 1 or 2.")

    img = validate_png_image(image_input)
    width, height = img.size
    cap = calculate_capacity(img, lsb_bits=lsb_bits)

    if len(secret_payload) > cap["usable_payload_bytes"]:
        raise SteganographyError(
            f"Payload size ({len(secret_payload)} bytes) exceeds usable image capacity "
            f"({cap['usable_payload_bytes']} bytes)."
        )

    # Header: Magic marker (4 bytes) + Payload length (4 bytes uint32 big-endian)
    header = MAGIC_MARKER + struct.pack(">I", len(secret_payload))
    full_payload = header + secret_payload

    # Convert payload bytes to array of bits (0 or 1)
    payload_bits = np.unpackbits(np.frombuffer(full_payload, dtype=np.uint8))
    
    pixels = np.array(img, dtype=np.uint8)
    flat = pixels.flatten()

    if lsb_bits == 1:
        num_bits = len(payload_bits)
        mask = np.uint8(0xFE)  # 0b11111110
        flat[:num_bits] = (flat[:num_bits] & mask) | payload_bits
    elif lsb_bits == 2:
        if len(payload_bits) % 2 != 0:
            payload_bits = np.append(payload_bits, np.uint8(0))
        pairs = payload_bits.reshape(-1, 2)
        pair_vals = ((pairs[:, 0] << 1) | pairs[:, 1]).astype(np.uint8)
        num_pixels = len(pair_vals)
        mask = np.uint8(0xFC)  # 0b11111100
        flat[:num_pixels] = (flat[:num_pixels] & mask) | pair_vals

    stego_img = Image.fromarray(flat.reshape((height, width, 3)), mode="RGB")
    buf = io.BytesIO()
    stego_img.save(buf, format="PNG")
    return buf.getvalue()

def decode_message(image_input: bytes | str | Image.Image, lsb_bits: int = 1) -> bytes:
    """
    Extract embedded binary payload from a PNG stego image.
    Validates magic marker header and declared length.
    """
    if lsb_bits not in (1, 2):
        raise SteganographyError("LSB bits per channel must be 1 or 2.")

    img = validate_png_image(image_input)
    pixels = np.array(img, dtype=np.uint8)
    flat = pixels.flatten()

    header_bytes_needed = HEADER_SIZE  # 8 bytes
    header_bits_needed = header_bytes_needed * 8  # 64 bits

    if lsb_bits == 1:
        if len(flat) < header_bits_needed:
            raise SteganographyError("Image is too small to contain a StegoShield payload header.")
        header_bits = flat[:header_bits_needed] & 1
        header_bytes = np.packbits(header_bits).tobytes()
    else:
        num_px = header_bits_needed // 2  # 32 pixels
        if len(flat) < num_px:
            raise SteganographyError("Image is too small to contain a StegoShield payload header.")
        px_vals = flat[:num_px] & 3
        header_bits = np.empty(header_bits_needed, dtype=np.uint8)
        header_bits[0::2] = (px_vals >> 1) & 1
        header_bits[1::2] = px_vals & 1
        header_bytes = np.packbits(header_bits).tobytes()

    magic = header_bytes[:4]
    if magic != MAGIC_MARKER:
        raise SteganographyError("Header check failed: Image does not contain StegoShield steganographic data.")

    payload_length = struct.unpack(">I", header_bytes[4:8])[0]
    total_bytes_needed = HEADER_SIZE + payload_length
    total_bits_needed = total_bytes_needed * 8

    if lsb_bits == 1:
        if len(flat) < total_bits_needed:
            raise SteganographyError("Corrupted image: Image pixel count is smaller than declared payload length.")
        extracted_bits = flat[:total_bits_needed] & 1
    else:
        num_px_needed = (total_bits_needed + 1) // 2
        if len(flat) < num_px_needed:
            raise SteganographyError("Corrupted image: Image pixel count is smaller than declared payload length.")
        px_vals = flat[:num_px_needed] & 3
        extracted_bits = np.empty(num_px_needed * 2, dtype=np.uint8)
        extracted_bits[0::2] = (px_vals >> 1) & 1
        extracted_bits[1::2] = px_vals & 1
        extracted_bits = extracted_bits[:total_bits_needed]

    full_payload = np.packbits(extracted_bits).tobytes()
    payload = full_payload[HEADER_SIZE : HEADER_SIZE + payload_length]

    if len(payload) != payload_length:
        raise SteganographyError("Validation failed: Extracted payload size does not match header declaration.")

    return payload

def encode_secret_with_password(image_input: bytes | str | Image.Image, secret_message: str, password: str, lsb_bits: int = 1) -> bytes:
    """Convenience function: Encrypt message with password and embed into PNG image."""
    encrypted_payload = encrypt_message(secret_message, password)
    return encode_message(image_input, encrypted_payload, lsb_bits=lsb_bits)

def decode_secret_with_password(image_input: bytes | str | Image.Image, password: str, lsb_bits: int = 1) -> str:
    """Convenience function: Extract payload from PNG image and decrypt with password."""
    extracted_payload = decode_message(image_input, lsb_bits=lsb_bits)
    try:
        return decrypt_message(extracted_payload, password)
    except EncryptionError as e:
        raise SteganographyError(f"Decryption failed: {str(e)}")
