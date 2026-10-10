"""
StegoShield Baseline Steganalysis & Statistical Anomaly Detection Module.

FOR STEGANALYSIS DEMONSTRATION & VERIFICATION:
This module performs statistical steganalysis to evaluate whether an image exhibits
anomalous characteristics associated with Least-Significant Bit (LSB) steganography.

ALGORITHM EXPLANATION & METHODOLOGY:
1. RGB Channel Statistics: Measures mean, variance, and standard deviation across channels.
2. LSB Zero/One Ratio: Natural images rarely have an exact 50/50 LSB bit split. Encrypted stego data forces 50% 0s and 50% 1s.
3. Chi-Square (X^2) PoVs Test: Compares frequencies of adjacent pixel pairs (2k and 2k+1). LSB embedding equalizes these pairs.
4. Neighboring Pixel Correlation: Natural image LSBs are correlated with adjacent pixels. Random payload embedding destroys this spatial correlation.
5. Interpretable Suspicion Score: Aggregates features into a 0-100 score categorized as LOW, MEDIUM, or HIGH statistical anomaly.

IMPORTANT DISCLAIMER:
This module provides a 'Statistical Anomaly / Suspicion Indication' and does NOT claim definitive proof of hidden data.
"""

import io
import math
import numpy as np
from PIL import Image

class SteganalysisError(Exception):
    """Custom exception for steganalysis module errors."""
    pass

DISCLAIMER_TEXT = (
    "Disclaimer: Steganalysis provides a 'Statistical Anomaly / Suspicion Indication' based on "
    "pixel distribution metrics. It does NOT claim definitive determination of hidden information."
)

def compute_shannon_entropy(bits: np.ndarray) -> float:
    """Compute Shannon entropy H(X) = -p0 log2(p0) - p1 log2(p1) for binary LSB array."""
    if len(bits) == 0:
        return 0.0
    p1 = float(np.mean(bits))
    p0 = 1.0 - p1
    if p0 <= 0.0 or p1 <= 0.0:
        return 0.0
    return float(-p0 * math.log2(p0) - p1 * math.log2(p1))

def compute_adjacent_lsb_correlation(lsb_plane: np.ndarray) -> float:
    """Calculate horizontal neighboring pixel LSB correlation coefficient."""
    if lsb_plane.shape[1] < 2:
        return 0.0
    left_pixels = lsb_plane[:, :-1].flatten().astype(np.float64)
    right_pixels = lsb_plane[:, 1:].flatten().astype(np.float64)
    
    std_left = np.std(left_pixels)
    std_right = np.std(right_pixels)
    if std_left == 0 or std_right == 0:
        return 0.0
        
    cov = np.cov(left_pixels, right_pixels)[0, 1]
    corr = cov / (std_left * std_right)
    return float(np.clip(corr, -1.0, 1.0))

def compute_chi_square_povs(channel_arr: np.ndarray) -> dict:
    """
    Perform Chi-Square (X^2) Pairs of Values (PoVs) test on a single channel.
    Pairs (0,1), (2,3), ..., (254,255) are expected to equalize after LSB embedding.
    """
    flat = channel_arr.flatten().astype(np.int32)
    counts = np.bincount(flat, minlength=256)

    counts_even = counts[0::2]
    counts_odd = counts[1::2]
    expected = (counts_even + counts_odd) / 2.0

    valid_mask = expected > 0
    if not np.any(valid_mask):
        return {"chi2_stat": 0.0, "dof": 0, "anomaly_score": 0.0, "chi2": 0.0, "suspicion_percent": 0.0}

    obs_even = counts_even[valid_mask]
    exp = expected[valid_mask]

    chi2_stat = float(np.sum(((obs_even - exp) ** 2) / exp))
    dof = int(len(exp))

    normalized_ratio = chi2_stat / max(1, dof)
    
    # Low normalized_ratio (< 0.5) indicates high LSB pair equalization (high anomaly)
    if normalized_ratio < 0.2:
        anomaly_score = 95.0 + (0.2 - normalized_ratio) * 25.0
    elif normalized_ratio < 1.0:
        anomaly_score = 50.0 + (1.0 - normalized_ratio) * 50.0
    else:
        anomaly_score = max(0.0, 50.0 - (normalized_ratio - 1.0) * 10.0)

    anomaly_score = float(np.clip(anomaly_score, 0.0, 100.0))

    return {
        "chi2_stat": round(chi2_stat, 2),
        "chi2": round(chi2_stat, 2),
        "dof": dof,
        "normalized_ratio": round(normalized_ratio, 4),
        "anomaly_score": round(anomaly_score, 2),
        "suspicion_percent": round(anomaly_score, 2),
    }

def analyze_image_steganalysis(image_input: bytes | str | Image.Image) -> dict:
    """
    Analyze image for LSB steganography statistical anomaly characteristics.
    
    Returns structured dict:
    - feature_values: RGB stats, zero/one ratios, entropy, neighbor correlations, Chi2 stats.
    - suspicion_score: 0-100 overall score.
    - indication: "LOW" | "MEDIUM" | "HIGH" statistical anomaly indication.
    - viva_explanations: Explainable summary for steganography analysis.
    - disclaimer: Explicit limitations notice.
    """
    try:
        if isinstance(image_input, (bytes, bytearray)):
            img = Image.open(io.BytesIO(image_input))
        elif isinstance(image_input, str):
            img = Image.open(image_input)
        elif isinstance(image_input, Image.Image):
            img = image_input
        else:
            raise SteganalysisError("Unsupported image input type.")

        img_rgb = img.convert("RGB")
        arr = np.array(img_rgb, dtype=np.uint8)
    except Exception as e:
        raise SteganalysisError(f"Failed to open image for steganalysis: {str(e)}")

    height, width, _ = arr.shape
    total_pixels = width * height

    # 1. RGB Channel Statistics
    r_channel = arr[:, :, 0]
    g_channel = arr[:, :, 1]
    b_channel = arr[:, :, 2]

    rgb_stats = {
        "red": {"mean": round(float(np.mean(r_channel)), 2), "std": round(float(np.std(r_channel)), 2)},
        "green": {"mean": round(float(np.mean(g_channel)), 2), "std": round(float(np.std(g_channel)), 2)},
        "blue": {"mean": round(float(np.mean(b_channel)), 2), "std": round(float(np.std(b_channel)), 2)},
    }

    # 2. LSB Bit Distribution & Zero/One Ratio
    lsb_r = r_channel & 1
    lsb_g = g_channel & 1
    lsb_b = b_channel & 1

    all_lsbs = (arr & 1).flatten()
    ones_count = int(np.sum(all_lsbs))
    zeros_count = int(len(all_lsbs) - ones_count)
    zero_one_ratio = round(zeros_count / max(1, len(all_lsbs)), 4)
    lsb_entropy = round(compute_shannon_entropy(all_lsbs), 4)

    # 3. Neighboring Pixel Correlation
    r_corr = round(compute_adjacent_lsb_correlation(lsb_r), 4)
    g_corr = round(compute_adjacent_lsb_correlation(lsb_g), 4)
    b_corr = round(compute_adjacent_lsb_correlation(lsb_b), 4)
    avg_neighbor_corr = round((r_corr + g_corr + b_corr) / 3.0, 4)

    # 4. Chi-Square PoVs Test per Channel
    r_chi = compute_chi_square_povs(r_channel)
    g_chi = compute_chi_square_povs(g_channel)
    b_chi = compute_chi_square_povs(b_channel)
    avg_chi_anomaly = round((r_chi["anomaly_score"] + g_chi["anomaly_score"] + b_chi["anomaly_score"]) / 3.0, 2)

    # 5. Interpretable Suspicion Score Aggregation (0 - 100)
    ratio_deviation = abs(zero_one_ratio - 0.5)
    ratio_score = max(0.0, (0.05 - ratio_deviation) / 0.05) * 30.0 if ratio_deviation <= 0.05 else 0.0
    entropy_score = max(0.0, (lsb_entropy - 0.95) / 0.05) * 30.0 if lsb_entropy >= 0.95 else 0.0
    chi_score = (avg_chi_anomaly / 100.0) * 30.0
    corr_score = max(0.0, (0.1 - abs(avg_neighbor_corr)) / 0.1) * 10.0 if abs(avg_neighbor_corr) <= 0.1 else 0.0

    raw_suspicion = ratio_score + entropy_score + chi_score + corr_score
    suspicion_score = round(float(np.clip(raw_suspicion, 0.0, 100.0)), 2)

    # Indication Category: LOW / MEDIUM / HIGH
    if suspicion_score >= 70.0:
        indication = "HIGH"
        risk_class = "danger"
    elif suspicion_score >= 40.0:
        indication = "MEDIUM"
        risk_class = "warning"
    else:
        indication = "LOW"
        risk_class = "success"

    return {
        "indication": indication,
        "suspicion_score": suspicion_score,
        "avg_suspicion_percent": suspicion_score,
        "risk_level": f"{indication} ANOMALY",
        "risk_class": risk_class,
        "shannon_entropy": lsb_entropy,
        "feature_values": {
            "dimensions": f"{width}x{height}",
            "total_pixels": total_pixels,
            "rgb_stats": rgb_stats,
            "lsb_distribution": {
                "zeros_count": zeros_count,
                "ones_count": ones_count,
                "zero_one_ratio": zero_one_ratio,
                "shannon_entropy": lsb_entropy,
            },
            "neighbor_correlation": {
                "red_corr": r_corr,
                "green_corr": g_corr,
                "blue_corr": b_corr,
                "avg_neighbor_corr": avg_neighbor_corr,
            },
            "chi_square_povs": {
                "red": r_chi,
                "green": g_chi,
                "blue": b_chi,
                "avg_chi_anomaly": avg_chi_anomaly,
            },
        },
        "channel_analysis": {
            "red": r_chi,
            "green": g_chi,
            "blue": b_chi,
        },
        "viva_explanations": {
            "zero_one_ratio": f"Zero/One Ratio is {zero_one_ratio}. Ratios near 0.5000 indicate randomized LSB bit distribution.",
            "shannon_entropy": f"Shannon Entropy is {lsb_entropy}. Values close to 1.0000 suggest high-entropy encrypted payload embedding.",
            "chi_square_povs": f"Chi-Square PoVs anomaly score is {avg_chi_anomaly}%. Small Chi2 values indicate pixel pair frequency equalization.",
            "neighbor_correlation": f"Average Neighbor Correlation is {avg_neighbor_corr}. Values close to 0.0 indicate destruction of spatial LSB correlation.",
        },
        "disclaimer": DISCLAIMER_TEXT,
    }
