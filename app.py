import os
import io
import base64
from flask import Flask, render_template, request, jsonify
from config import Config
from encryption import encrypt_message, decrypt_message, EncryptionError
from steganography import encode_message, decode_message, SteganographyError
from capacity import (
    calculate_image_capacity,
    validate_capacity_before_encoding,
    CapacityError,
)
from analysis import analyze_image_quality, AnalysisError
from tamper_detection import verify_stego_integrity, simulate_image_manipulation, LIMITATIONS_NOTICE
from steganalysis import analyze_image_steganalysis, SteganalysisError, DISCLAIMER_TEXT

app = Flask(__name__)
app.config.from_object(Config)

# Ensure required upload and output directories exist
os.makedirs("uploads", exist_ok=True)
os.makedirs("outputs", exist_ok=True)

# --- 8 Page Routes ---

@app.route("/")
def home():
    """1. Dashboard Page"""
    return render_template("index.html", active_page="home")

@app.route("/encode")
def encode_page():
    """2. Encode Page"""
    return render_template("encode.html", active_page="encode")

@app.route("/decode")
def decode_page():
    """3. Decode Page"""
    return render_template("decode.html", active_page="decode")

@app.route("/image-analysis")
@app.route("/analyze")
def analyze_page():
    """4. Image Quality Analysis Page (MSE, PSNR, SSIM)"""
    return render_template("analyze.html", active_page="analyze")

@app.route("/tamper-detection")
def tamper_page():
    """5. Tamper Detection & Integrity Verification Page"""
    return render_template("tamper.html", active_page="tamper")

@app.route("/steganalysis")
def steganalysis_page():
    """6. Baseline Steganalysis & Statistical Anomaly Page"""
    return render_template("steganalysis_page.html", active_page="steganalysis")

@app.route("/history")
def history_page():
    """7. Session History Logs Page"""
    return render_template("history.html", active_page="history")

@app.route("/about")
def about_page():
    """8. About & Technical Architecture Page"""
    return render_template("about.html", active_page="about")


# --- REST API Endpoints ---

@app.route("/api/capacity", methods=["POST"])
def check_capacity():
    """Calculate embedding capacity of an uploaded cover image and message size."""
    if "image" not in request.files:
        return jsonify({"success": False, "error": "No image file provided."}), 400

    file = request.files["image"]
    secret_text = request.form.get("secret_text", "")
    lsb_count = int(request.form.get("lsb_count", 1))

    try:
        img_bytes = file.read()
        capacity_info = calculate_image_capacity(img_bytes, secret_text, lsb_bits=lsb_count)
        return jsonify({"success": True, "capacity": capacity_info})
    except (CapacityError, Exception) as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/embed", methods=["POST"])
def embed_secret():
    """
    Encoding Flow:
    1. Validate capacity before encoding.
    2. Password Encryption -> Encrypted Payload.
    3. LSB Embedding -> Stego PNG.
    4. Compute Quality Metrics (MSE, PSNR, SSIM) using actual pixel arrays.
    """
    if "cover_image" not in request.files:
        return jsonify({"success": False, "error": "Cover image file is required."}), 400

    file = request.files["cover_image"]
    secret_text = request.form.get("secret_text", "")
    password = request.form.get("password", "").strip()
    lsb_count = int(request.form.get("lsb_count", 1))

    if not secret_text:
        return jsonify({"success": False, "error": "Secret message cannot be empty."}), 400
    if not password:
        return jsonify({"success": False, "error": "Password cannot be empty."}), 400

    try:
        cover_bytes = file.read()

        # Validate capacity before encoding
        capacity_info = validate_capacity_before_encoding(cover_bytes, secret_text, lsb_bits=lsb_count)

        # Encrypt secret message using password
        encrypted_payload = encrypt_message(secret_text, password)

        # Embed encrypted payload into PNG LSBs with metadata header
        stego_png_bytes = encode_message(cover_bytes, encrypted_payload, lsb_bits=lsb_count)

        # Calculate distortion quality metrics (MSE, PSNR, SSIM) from actual pixel arrays
        metrics = analyze_image_quality(cover_bytes, stego_png_bytes)

        # Save copy to outputs directory
        output_filename = "stego_shield_output.png"
        output_filepath = os.path.join("outputs", output_filename)
        with open(output_filepath, "wb") as f:
            f.write(stego_png_bytes)

        # Base64 string for immediate frontend preview & download
        stego_b64 = base64.b64encode(stego_png_bytes).decode("ascii")
        stego_data_uri = f"data:image/png;base64,{stego_b64}"

        return jsonify({
            "success": True,
            "stego_image_b64": stego_data_uri,
            "filename": output_filename,
            "stats": capacity_info,
            "metrics": metrics,
        })
    except (CapacityError, EncryptionError, SteganographyError, AnalysisError) as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Encoding failed: {str(e)}"}), 500

@app.route("/api/extract", methods=["POST"])
def extract_secret():
    """
    Decoding & Tamper Verification Flow:
    Uses verify_stego_integrity() to check magic header, AEAD MAC tag, and returns status:
    - "Likely Unmodified"
    - "Possible Tampering"
    - "Corrupted / Extraction Failed"
    """
    if "stego_image" not in request.files:
        return jsonify({"success": False, "error": "Stego image file is required."}), 400

    file = request.files["stego_image"]
    password = request.form.get("password", "").strip()

    if not password:
        return jsonify({"success": False, "error": "Password is required for extraction."}), 400

    try:
        stego_bytes = file.read()

        result = verify_stego_integrity(stego_bytes, password)

        if result["is_authentic"]:
            return jsonify({
                "success": True,
                "status": result["status"],
                "secret_message": result["decrypted_message"],
                "lsb_count": 1,
                "tampered": False,
                "limitations_notice": result["limitations_notice"],
            })
        else:
            return jsonify({
                "success": False,
                "status": result["status"],
                "tampered": True,
                "error": result["error_details"],
                "limitations_notice": result["limitations_notice"],
            }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "status": "Corrupted / Extraction Failed",
            "error": f"Extraction failed: {str(e)}",
            "limitations_notice": LIMITATIONS_NOTICE,
        }), 500

@app.route("/api/tamper/simulate", methods=["POST"])
def simulate_tamper():
    """Simulate image manipulation (pixel modify, resize, crop, filter, recompress) for tamper testing."""
    if "stego_image" not in request.files:
        return jsonify({"success": False, "error": "Stego image file is required."}), 400

    file = request.files["stego_image"]
    action = request.form.get("action", "modify_pixel")

    try:
        image_bytes = file.read()
        manipulated_bytes = simulate_image_manipulation(image_bytes, action)
        manipulated_b64 = base64.b64encode(manipulated_bytes).decode("ascii")
        return jsonify({
            "success": True,
            "action": action,
            "manipulated_image_b64": f"data:image/png;base64,{manipulated_b64}",
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/analyze", methods=["POST"])
def analyze_image():
    """
    Perform statistical steganalysis:
    - RGB channel statistics
    - LSB zero/one ratio & Shannon entropy
    - Chi-Square PoVs test
    - Neighboring pixel correlation
    - Suspicion score (0-100) & LOW/MEDIUM/HIGH indication
    """
    if "image" not in request.files:
        return jsonify({"success": False, "error": "Image file is required."}), 400

    file = request.files["image"]

    try:
        img_bytes = file.read()
        report = analyze_image_steganalysis(img_bytes)
        return jsonify({"success": True, "report": report})
    except (SteganalysisError, Exception) as e:
        return jsonify({"success": False, "error": str(e)}), 400

@app.route("/api/compare", methods=["POST"])
def compare_images():
    """Compare Cover image and Stego image to generate actual MSE, PSNR, SSIM quality report."""
    if "cover_image" not in request.files or "stego_image" not in request.files:
        return jsonify({"success": False, "error": "Both cover and stego images are required."}), 400

    cover_file = request.files["cover_image"]
    stego_file = request.files["stego_image"]

    try:
        cover_bytes = cover_file.read()
        stego_bytes = stego_file.read()

        metrics = analyze_image_quality(cover_bytes, stego_bytes)
        return jsonify({"success": True, "metrics": metrics})
    except AnalysisError as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

def is_streamlit_running() -> bool:
    """Detect if current execution is initiated by Streamlit Cloud runner."""
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx() is not None:
            return True
    except Exception:
        pass
    if "STREAMLIT_SERVER_PORT" in os.environ:
        return True
    import sys
    return any("streamlit" in str(arg).lower() for arg in sys.argv)

if is_streamlit_running():
    from streamlit_app import main as streamlit_main
    streamlit_main()
elif __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
