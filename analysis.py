import io
import math
import numpy as np
from PIL import Image

class AnalysisError(Exception):
    """Custom exception for image quality analysis errors."""
    pass

def load_image_as_array(image_input: bytes | str | Image.Image) -> tuple[np.ndarray, tuple[int, int]]:
    """Load an image input into an RGB uint8 NumPy array and return (array, (width, height))."""
    try:
        if isinstance(image_input, (bytes, bytearray)):
            img = Image.open(io.BytesIO(image_input))
        elif isinstance(image_input, str):
            img = Image.open(image_input)
        elif isinstance(image_input, Image.Image):
            img = image_input
        else:
            raise AnalysisError("Unsupported image input type.")

        img_rgb = img.convert("RGB")
        return np.array(img_rgb, dtype=np.uint8), img_rgb.size
    except AnalysisError:
        raise
    except Exception as e:
        raise AnalysisError(f"Failed to process image: {str(e)}")

def calculate_mse(cover_arr: np.ndarray, stego_arr: np.ndarray) -> float:
    """
    Calculate Mean Squared Error (MSE) from actual pixel arrays.
    MSE = (1 / N) * SUM((Cover - Stego)^2)
    """
    if cover_arr.shape != stego_arr.shape:
        raise AnalysisError("Image dimensions must match to compute MSE.")

    diff = cover_arr.astype(np.float64) - stego_arr.astype(np.float64)
    mse_val = np.mean(diff ** 2)
    return float(mse_val)

def calculate_psnr(mse: float, max_pixel_val: float = 255.0) -> float:
    """
    Calculate Peak Signal-to-Noise Ratio (PSNR) in dB from MSE.
    PSNR = 10 * log10(MAX^2 / MSE)
    """
    if mse == 0:
        return 100.0  # Identical images benchmark
    
    psnr_val = 10.0 * math.log10((max_pixel_val ** 2) / mse)
    return float(psnr_val)

def calculate_ssim(cover_arr: np.ndarray, stego_arr: np.ndarray) -> float:
    """
    Calculate Structural Similarity Index Measure (SSIM) between cover and stego pixel arrays.
    SSIM evaluates luminance, contrast, and structural comparison.
    Range: -1.0 to 1.0 (1.0 = identical images).
    """
    if cover_arr.shape != stego_arr.shape:
        raise AnalysisError("Image dimensions must match to compute SSIM.")

    c = cover_arr.astype(np.float64)
    s = stego_arr.astype(np.float64)

    K1 = 0.01
    K2 = 0.03
    L = 255.0

    C1 = (K1 * L) ** 2
    C2 = (K2 * L) ** 2

    mu_c = np.mean(c)
    mu_s = np.mean(s)

    var_c = np.var(c)
    var_s = np.var(s)
    cov_cs = np.cov(c.flatten(), s.flatten())[0, 1]

    numerator = (2 * mu_c * mu_s + C1) * (2 * cov_cs + C2)
    denominator = (mu_c ** 2 + mu_s ** 2 + C1) * (var_c + var_s + C2)

    ssim_val = numerator / denominator
    return float(np.clip(ssim_val, -1.0, 1.0))

def analyze_image_quality(cover_input: bytes | str | Image.Image, stego_input: bytes | str | Image.Image) -> dict:
    """
    Perform full image quality comparison between original cover and generated stego image.
    Calculates actual MSE, PSNR, SSIM, and pixel difference metrics from raw pixel arrays.
    """
    arr_cover, size_cover = load_image_as_array(cover_input)
    arr_stego, size_stego = load_image_as_array(stego_input)

    if size_cover != size_stego:
        raise AnalysisError(
            f"Image dimension mismatch: Cover is {size_cover[0]}x{size_cover[1]} px, "
            f"Stego is {size_stego[0]}x{size_stego[1]} px."
        )

    mse = calculate_mse(arr_cover, arr_stego)
    psnr = calculate_psnr(mse)
    ssim = calculate_ssim(arr_cover, arr_stego)

    diff = np.abs(arr_cover.astype(np.int16) - arr_stego.astype(np.int16))
    max_pixel_diff = int(np.max(diff))

    # Count pixels with at least 1 modified RGB channel
    pixel_changes = np.any(diff > 0, axis=2)
    modified_pixels = int(np.sum(pixel_changes))
    total_pixels = size_cover[0] * size_cover[1]
    percent_pixels_modified = round((modified_pixels / max(1, total_pixels)) * 100, 2)

    # Educational explanations suitable for college demonstration
    if psnr >= 50.0:
        psnr_quality = "Exceptional (Stego modifications completely imperceptible)"
    elif psnr >= 40.0:
        psnr_quality = "High Quality (Steganography within human visual limit)"
    else:
        psnr_quality = "Noticeable Distortion"

    return {
        "dimensions": f"{size_cover[0]}x{size_cover[1]}",
        "total_pixels": total_pixels,
        "mse": round(mse, 6),
        "psnr": round(psnr, 2) if psnr != float("inf") else 100.0,
        "ssim": round(ssim, 6),
        "max_pixel_diff": max_pixel_diff,
        "modified_pixels": modified_pixels,
        "percent_pixels_modified": percent_pixels_modified,
        "explanations": {
            "mse": "Mean Squared Error: Measures average squared difference between cover and stego pixels. Values closer to 0 represent lower distortion.",
            "psnr": f"Peak Signal-to-Noise Ratio: Evaluates image fidelity in decibels (dB). PSNR > 40 dB indicates high visual imperceptibility. Assessment: {psnr_quality}.",
            "ssim": "Structural Similarity Index: Evaluates structural, luminance, and contrast similarity. Range: -1.0 to 1.0 (1.0 indicates identical images).",
        }
    }
