import io
import math
import pytest
from PIL import Image
import numpy as np
from analysis import (
    calculate_mse,
    calculate_psnr,
    calculate_ssim,
    analyze_image_quality,
    AnalysisError,
)

def create_solid_png(width=100, height=100, color=(128, 128, 128)) -> bytes:
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def test_identical_images():
    """1. Test metrics calculation for identical cover and stego images."""
    img_bytes = create_solid_png(50, 50)
    report = analyze_image_quality(img_bytes, img_bytes)

    assert report["mse"] == 0.0
    assert report["psnr"] == 100.0
    assert report["ssim"] == 1.0
    assert report["modified_pixels"] == 0
    assert report["percent_pixels_modified"] == 0.0

def test_controlled_pixel_modification():
    """
    2. Controlled synthetic test image:
    Create a 100x100 RGB image (30,000 channel values).
    Modify exactly 1 channel value by +1 in 1 pixel.
    Theoretical MSE = 1 / 30000 = 0.000033333...
    Theoretical PSNR = 10 * log10(255^2 / (1/30000)) ~ 92.90 dB
    """
    arr1 = np.full((100, 100, 3), 128, dtype=np.uint8)
    arr2 = arr1.copy()
    arr2[0, 0, 0] = 129  # 1 bit modification

    img1 = Image.fromarray(arr1, mode="RGB")
    img2 = Image.fromarray(arr2, mode="RGB")

    buf1, buf2 = io.BytesIO(), io.BytesIO()
    img1.save(buf1, format="PNG")
    img2.save(buf2, format="PNG")

    report = analyze_image_quality(buf1.getvalue(), buf2.getvalue())

    expected_mse = 1.0 / (100 * 100 * 3)
    expected_psnr = 10.0 * math.log10((255.0 ** 2) / expected_mse)

    assert pytest.approx(report["mse"], abs=1e-5) == expected_mse
    assert pytest.approx(report["psnr"], abs=1e-2) == expected_psnr
    assert report["ssim"] > 0.999
    assert report["modified_pixels"] == 1

def test_dimension_mismatch_raises_error():
    """3. Test dimension mismatch error handling."""
    img1 = create_solid_png(50, 50)
    img2 = create_solid_png(60, 60)

    with pytest.raises(AnalysisError) as exc_info:
        analyze_image_quality(img1, img2)
    assert "Image dimension mismatch" in str(exc_info.value)
