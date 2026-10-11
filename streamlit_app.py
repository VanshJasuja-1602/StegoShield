"""
StegnoShield - Streamlit Cloud Web Application
Provides a complete, interactive cybersecurity dashboard for StegnoShield:
- Encode (AES-256-GCM + PBKDF2 + RGB LSB Embedding)
- Decode & Tamper Detection (AEAD MAC Verification)
- Steganalysis (Chi-Square, Entropy, Suspicion Score)
- Architecture & Technical Specs
"""

import io
import streamlit as st
from PIL import Image

from capacity import calculate_image_capacity, validate_capacity_before_encoding, CapacityError
from encryption import encrypt_message, decrypt_message, EncryptionError
from steganography import encode_message, decode_message, SteganographyError
from analysis import analyze_image_quality, AnalysisError
from tamper_detection import verify_stego_integrity, simulate_image_manipulation, LIMITATIONS_NOTICE
from steganalysis import analyze_image_steganalysis, SteganalysisError, DISCLAIMER_TEXT

def apply_custom_theme():
    st.markdown("""
    <style>
    /* Dark Cyber Theme */
    .stApp {
        background-color: #080b17;
        color: #eef0fb;
    }
    
    /* Header & Accents */
    h1, h2, h3, h4 {
        color: #eef0fb !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #0d1124;
        padding: 8px;
        border-radius: 12px;
        border: 1px solid rgba(160, 170, 255, 0.15);
    }
    
    .stTabs [data-baseweb="tab"] {
        color: #a9aec8;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(120deg, #6d4dff 0%, #8f74ff 100%) !important;
        color: #ffffff !important;
    }
    
    /* Cards and metrics */
    .cyber-card {
        background: rgba(13, 17, 33, 0.85);
        border: 1.5px solid rgba(220, 175, 55, 0.75);
        box-shadow: 0 0 18px rgba(212, 175, 55, 0.15);
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 20px;
    }

    .cyber-card-glow {
        background: rgba(13, 17, 33, 0.85);
        border: 1.5px solid rgba(255, 255, 255, 0.85);
        box-shadow: 0 0 22px rgba(255, 255, 255, 0.35);
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 20px;
    }

    .stButton>button {
        background: linear-gradient(120deg, #6d4dff 0%, #8f74ff 50%, #5fd5f0 100%);
        color: #ffffff;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        padding: 10px 24px;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(143, 116, 255, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="StegnoShield",
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    apply_custom_theme()

    # Sidebar branding & info
    with st.sidebar:
        st.title("🛡️ StegnoShield")
        st.caption("Secure Image Steganography & Steganalysis")
        st.markdown("---")
        st.markdown("""
        **Security Engine:**
        - 🔒 **Cipher:** AES-256-GCM
        - 🔑 **KDF:** PBKDF2 HMAC SHA-256
        - 🖼️ **Embedding:** RGB LSB (1–2 bits)
        - 🛡️ **Integrity:** 128-bit AEAD MAC Tag
        - 📊 **Steganalysis:** $\chi^2$ PoVs & Entropy
        """)
        st.markdown("---")
        st.info("Zero-Persistence Mandate: Plaintext and passwords are processed strictly in-memory.")

    # Main Tabs
    tab_overview, tab_encode, tab_decode, tab_steganalysis, tab_about = st.tabs([
        "🏠 Dashboard",
        "🔒 Encode Message",
        "🔓 Decode & Tamper Check",
        "📊 Steganalysis",
        "ℹ️ About"
    ])

    # 1. OVERVIEW / DASHBOARD TAB
    with tab_overview:
        st.markdown("## Hide. Protect. Verify. *Inside every image.*")
        st.markdown(
            "Secure your messages with **AES-256 encryption**, hide them inside images, "
            "and detect tampering or suspicious patterns in real time."
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
            <div class="cyber-card">
                <h4>🔒 Encode & Decode</h4>
                <p>Encrypt confidential text using AES-256-GCM and hide it inside the RGB least-significant bits of lossless PNG images.</p>
                <small style="color: #8f74ff;">AES-256-GCM + LSB</small>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
            <div class="cyber-card">
                <h4>⚠️ Tamper Detection</h4>
                <p>Cryptographic AEAD MAC tags instantly flag bit flips, cropping, resizing, lossy recompression, or pixel filtering.</p>
                <small style="color: #f5b544;">16-Byte AEAD MAC</small>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
            <div class="cyber-card">
                <h4>📊 Steganalysis</h4>
                <p>Inspect any image for statistical LSB anomalies (RGB statistics, Shannon entropy, Chi-Square PoVs) with suspicion scores.</p>
                <small style="color: #67e8f9;">χ² · Entropy</small>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("### Protocol Workflow")
        w1, w2, w3, w4, w5 = st.columns(5)
        w1.metric("Step 1", "Upload PNG", "Lossless format")
        w2.metric("Step 2", "Encrypt", "AES-256-GCM")
        w3.metric("Step 3", "LSB Embed", "1-2 bits/channel")
        w4.metric("Step 4", "AEAD Check", "MAC verification")
        w5.metric("Step 5", "Extract", "Plaintext payload")

    # 2. ENCODE TAB
    with tab_encode:
        st.subheader("Encode & Hide a Secret Message")
        st.caption("Encrypt payload with password-derived AES-256-GCM key and hide into PNG cover image pixels.")

        enc_col1, enc_col2 = st.columns([1, 1])

        with enc_col1:
            cover_file = st.file_uploader("1. Select Cover Image (PNG / BMP)", type=["png", "bmp"], key="cover_upload")
            secret_text = st.text_area("2. Secret Message Payload", placeholder="Enter confidential message to hide...", height=120)
            password = st.text_input("3. Encryption Password", type="password", placeholder="Enter secret password", key="enc_pw")
            lsb_count = st.selectbox(
                "4. LSB Bit Depth",
                options=[1, 2],
                format_func=lambda x: f"{x} Bit per Channel ({'Maximum Quality' if x == 1 else 'Higher Capacity'})"
            )

            # Live Capacity Check
            if cover_file and secret_text:
                try:
                    cover_bytes = cover_file.getvalue()
                    cap = calculate_image_capacity(cover_bytes, secret_text, lsb_bits=lsb_count)
                    pct = cap["used_percentage"]
                    st.progress(min(pct / 100.0, 1.0))
                    c_a, c_b, c_c = st.columns(3)
                    c_a.metric("Total Capacity", f"{cap['total_capacity_bytes']:,} B")
                    c_b.metric("Payload Size", f"{cap['encrypted_payload_size_bytes']:,} B")
                    c_c.metric("Used", f"{pct:.2f}%")
                    if cap["is_exceeded"]:
                        st.error("⚠️ Payload exceeds available image capacity! Please use a larger image or fewer characters.")
                except Exception as e:
                    st.warning(f"Capacity check notice: {str(e)}")

            encode_btn = st.button("🔒 Encrypt & Embed Secret Message", use_container_width=True)

        with enc_col2:
            if encode_btn:
                if not cover_file:
                    st.error("Please upload a cover image first.")
                elif not secret_text.strip():
                    st.error("Please provide a secret message to embed.")
                elif not password.strip():
                    st.error("Password is required for encryption.")
                else:
                    with st.spinner("Encrypting payload and embedding into pixels..."):
                        try:
                            cover_bytes = cover_file.getvalue()
                            # 1. Capacity validation
                            validate_capacity_before_encoding(cover_bytes, secret_text, lsb_bits=lsb_count)
                            # 2. Encryption
                            encrypted_payload = encrypt_message(secret_text, password)
                            # 3. LSB embedding
                            stego_png_bytes = encode_message(cover_bytes, encrypted_payload, lsb_bits=lsb_count)
                            # 4. Quality distortion metrics
                            metrics = analyze_image_quality(cover_bytes, stego_png_bytes)

                            st.success("✅ Secret message successfully encrypted and embedded!")
                            
                            st.image(stego_png_bytes, caption="Generated Stego PNG Image", use_container_width=True)

                            st.download_button(
                                label="⬇️ Download Stego PNG",
                                data=stego_png_bytes,
                                file_name="stego_shield_output.png",
                                mime="image/png",
                                use_container_width=True
                            )

                            st.markdown("#### Quality Distortion Metrics")
                            m1, m2, m3 = st.columns(3)
                            m1.metric("PSNR", f"{metrics['psnr']:.2f} dB", "Higher = less distortion")
                            m2.metric("SSIM", f"{metrics['ssim']:.4f}", "1.0 = identical structure")
                            m3.metric("MSE", f"{metrics['mse']:.6f}", "Pixel variance")

                            st.markdown(f"""
                            - **Modified Pixels:** {metrics['modified_pixels']:,} ({metrics['percent_pixels_modified']:.2f}%)
                            - **Max Channel Change:** ±{metrics['max_pixel_diff']}
                            """)
                        except (CapacityError, EncryptionError, SteganographyError, AnalysisError) as e:
                            st.error(f"Error: {str(e)}")
                        except Exception as e:
                            st.error(f"Encoding failed: {str(e)}")
            else:
                st.info("Upload an image, input your message and password, then click Encrypt & Embed.")

    # 3. DECODE & TAMPER CHECK TAB
    with tab_decode:
        st.subheader("Decode & Verify Payload Integrity")
        st.caption("Upload a stego PNG image and enter your password to extract and verify authenticity.")

        dec_col1, dec_col2 = st.columns([1, 1])

        with dec_col1:
            stego_file = st.file_uploader("1. Upload Stego PNG Image", type=["png", "bmp"], key="stego_upload")
            extract_password = st.text_input("2. Decryption Password", type="password", key="dec_pw")
            decode_btn = st.button("🔓 Verify Integrity & Extract Payload", use_container_width=True)

        with dec_col2:
            if decode_btn:
                if not stego_file:
                    st.error("Please upload a stego image.")
                elif not extract_password.strip():
                    st.error("Password is required for decryption.")
                else:
                    with st.spinner("Checking header and verifying AEAD MAC tag..."):
                        try:
                            stego_bytes = stego_file.getvalue()
                            result = verify_stego_integrity(stego_bytes, extract_password)

                            if result["is_authentic"]:
                                st.success("✅ Integrity Verified: Authentication tag matched!")
                                st.markdown("### Decrypted Secret Message:")
                                st.code(result["decrypted_message"], language="text")
                                st.info(f"Status: **{result['status']}**")
                            else:
                                st.error(f"❌ {result['status']}")
                                st.warning(f"Details: {result['error_details']}")
                                st.caption(result["limitations_notice"])
                        except Exception as e:
                            st.error(f"Extraction failed: {str(e)}")
            else:
                st.info("Upload the stego PNG and enter the password used during embedding.")

    # 4. STEGANALYSIS TAB
    with tab_steganalysis:
        st.subheader("Statistical Steganalysis & Anomaly Detection")
        st.caption("Inspect any image for statistical LSB anomalies (Chi-Square PoVs, bit balance, Shannon entropy).")

        steg_file = st.file_uploader("Select Image for Statistical Inspection", type=["png", "bmp"], key="steg_upload")
        if steg_file:
            with st.spinner("Calculating statistical features..."):
                try:
                    img_bytes = steg_file.getvalue()
                    report = analyze_image_steganalysis(img_bytes)

                    sc1, sc2 = st.columns([1, 2])
                    with sc1:
                        score = report["suspicion_score"]
                        ind = report["indication"]
                        if ind == "LOW":
                            st.success(f"Suspicion Score: {score}/100\n\nIndication: **{ind}** Anomaly")
                        elif ind == "MEDIUM":
                            st.warning(f"Suspicion Score: {score}/100\n\nIndication: **{ind}** Anomaly")
                        else:
                            st.error(f"Suspicion Score: {score}/100\n\nIndication: **{ind}** Anomaly")

                        st.image(img_bytes, caption="Inspected Image", use_container_width=True)

                    with sc2:
                        st.markdown("#### Feature Values")
                        fv = report["feature_values"]
                        f_col1, f_col2 = st.columns(2)
                        f_col1.metric("LSB 0/1 Ratio", f"{fv['lsb_zero_one_ratio']:.4f}", "Target ≈ 0.5000 for encrypted data")
                        f_col1.metric("Shannon Entropy", f"{fv['shannon_entropy']:.4f}", "Max = 1.0 bit/symbol")
                        f_col2.metric("Chi-Square (χ²)", f"{fv['chi_square_statistic']:.2f}")
                        f_col2.metric("Neighbor Correlation", f"{fv['neighbor_pixel_correlation']:.4f}", "Natural images have > 0.3")

                        st.markdown("#### Interpretations")
                        ve = report.get("viva_explanations", {})
                        if ve:
                            st.markdown(f"- **Bit Balance:** {ve.get('zero_one_ratio', '')}")
                            st.markdown(f"- **Pair Equalization:** {ve.get('chi_square_povs', '')}")
                            st.markdown(f"- **Spatial Correlation:** {ve.get('neighbor_correlation', '')}")

                        st.info(report.get("disclaimer", DISCLAIMER_TEXT))

                except Exception as e:
                    st.error(f"Analysis failed: {str(e)}")

    # 5. ABOUT TAB
    with tab_about:
        st.subheader("Technical Architecture & Project Overview")
        st.markdown("""
        **StegnoShield** implements an end-to-end authenticated cryptographic and steganographic system:
        
        ### Protocol Bitstream Layout
        Each stego PNG contains an in-memory bitstream embedded in spatial LSBs:
        - `b"STEG"` (4 Bytes): Protocol Magic Marker
        - `uint32` (4 Bytes): Encrypted Payload Length
        - `Salt` (16 Bytes): PBKDF2 HMAC SHA-256 Salt
        - `Nonce` (12 Bytes): AES-GCM Initialization Vector
        - `Ciphertext + Tag` (Variable + 16 Bytes): AES-256-GCM Encrypted Data and 128-bit MAC Tag
        
        ### Key Specifications
        - **Total Metadata Overhead:** Exactly 52 Bytes
        - **PBKDF2 Iterations:** 100,000 rounds with SHA-256
        - **Zero Data Persistence:** Payloads and passwords processed strictly in `io.BytesIO` streams.
        """)


if __name__ == "__main__":
    main()
