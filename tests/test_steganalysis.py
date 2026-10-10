import io
import pytest
from PIL import Image
import numpy as np
from steganography import encode_secret_with_password
from steganalysis import analyze_image_steganalysis, SteganalysisError, DISCLAIMER_TEXT

def create_gradient_png(width=120, height=120) -> bytes:
    """Create a normal natural-looking gradient PNG image."""
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    for i in range(height):
        for j in range(width):
            arr[i, j] = [(i * 2) % 256, (j * 3) % 256, (i + j) % 256]
    img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def test_normal_png_steganalysis():
    """1. Test normal PNG image yields feature values and LOW/MEDIUM indication."""
    normal_png = create_gradient_png(120, 120)
    report = analyze_image_steganalysis(normal_png)

    assert "indication" in report
    assert report["indication"] in ("LOW", "MEDIUM", "HIGH")
    assert 0.0 <= report["suspicion_score"] <= 100.0

    features = report["feature_values"]
    assert "rgb_stats" in features
    assert "lsb_distribution" in features
    assert "neighbor_correlation" in features
    assert "chi_square_povs" in features

    assert report["disclaimer"] == DISCLAIMER_TEXT

def test_stegoshield_generated_image_steganalysis():
    """2. Test Steganalysis on a StegoShield-generated stego image."""
    cover_png = create_gradient_png(150, 150)
    secret_text = "StegoShield Steganalysis Test Payload 2026!"
    password = "StegoPassword123"

    stego_png = encode_secret_with_password(cover_png, secret_text, password, lsb_bits=1)
    report = analyze_image_steganalysis(stego_png)

    assert report["indication"] in ("LOW", "MEDIUM", "HIGH")
    assert report["suspicion_score"] > 0.0
    assert "viva_explanations" in report
    assert "zero_one_ratio" in report["viva_explanations"]

def test_modified_image_steganalysis():
    """3. Test Steganalysis on a modified/randomized LSB image."""
    img_arr = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
    img = Image.fromarray(img_arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    mod_png = buf.getvalue()

    report = analyze_image_steganalysis(mod_png)

    assert report["indication"] in ("MEDIUM", "HIGH")
    assert report["suspicion_score"] >= 40.0
    assert report["disclaimer"] == DISCLAIMER_TEXT

def test_disclaimer_does_not_claim_definitive_proof():
    """4. Verify system explicitly describes output as statistical anomaly / suspicion indication."""
    png_bytes = create_gradient_png(50, 50)
    report = analyze_image_steganalysis(png_bytes)

    assert "Statistical Anomaly / Suspicion Indication" in report["disclaimer"]
    assert "does NOT claim definitive" in report["disclaimer"]
