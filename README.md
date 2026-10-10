# StegoShield - Secure Image Steganography with Tamper Detection & Steganalysis

StegoShield is a local web application built with Python 3.11+, Flask, Bootstrap 5, NumPy, Pillow, and `cryptography`. It enables users to encrypt text messages with AES-256-GCM, hide payloads inside PNG image LSBs, detect image tampering/corruption, evaluate image distortion metrics (MSE, PSNR, SSIM), and perform Chi-Square statistical steganalysis.

---

## Project Structure

```
StegoShield/
│
├── app.py                     # Flask web application routes & REST API
├── config.py                  # Protocol configuration & constants
├── encryption.py              # AES-256-GCM encryption, decryption & PBKDF2
├── steganography.py           # RGB LSB embedding / extraction engine
├── capacity.py                # Embedding capacity calculator
├── analysis.py                # MSE, PSNR, SSIM image quality metrics
├── tamper_detection.py        # Integrity verification & manipulation simulator
├── steganalysis.py            # Chi-Square PoVs, entropy & suspicion scoring
├── requirements.txt           # Python package dependencies
├── pytest.ini                 # Pytest automated test settings
├── README.md                  # Project documentation & setup guide
│
├── templates/                 # Jinja2 HTML templates (Bootstrap 5)
│   ├── base.html              # Layout, navigation, theme toggle & footer
│   ├── index.html             # Homepage dashboard
│   ├── encode.html            # Encode page
│   ├── decode.html            # Decode page
│   ├── analyze.html           # Image Comparison page (MSE / PSNR / SSIM)
│   ├── tamper.html            # Tamper Detection page
│   ├── steganalysis_page.html # Steganalysis page
│   ├── history.html           # Session activity history page
│   ├── about.html             # Project architecture & demo guide
│   └── components/            # Reusable UI component blocks
│       ├── embed_tab.html
│       ├── extract_tab.html
│       ├── metrics_tab.html
│       └── steganalysis_tab.html
│
├── static/                    # Frontend Static Assets
│   ├── css/
│   │   └── style.css          # Design system (dark + light themes)
│   └── js/
│       ├── main.js            # Interactive UI logic & AJAX handlers
│       ├── ui.js              # Presentation-only enhancements (theme, comparison, gauge)
│       ├── bg-animation.js    # Background constellation animation
│       └── chart_config.js    # Chart.js helper (currently unused)
│
├── uploads/                   # Uploads directory
├── outputs/                   # Outputs directory
│
└── tests/                     # Pytest Automated Test Suite (48 tests)
    ├── test_encryption.py
    ├── test_steganography.py
    ├── test_capacity.py
    ├── test_analysis.py
    ├── test_tamper_detection.py
    ├── test_steganalysis.py
    ├── test_routes.py
    └── test_all_13_workflows.py
```

---

## Core Functionality

1. **AES-256-GCM Encryption**: Key derived using PBKDF2HMAC SHA-256 (100,000 iterations).
2. **RGB LSB Steganography**: Custom LSB embedding supporting 1-bit and 2-bit per channel modes on PNG images.
3. **Capacity Calculator**: Pre-calculates exact embedding capacity prior to encryption.
4. **Tamper & Corruption Detection**: Checks 16-byte AEAD MAC tag upon decryption, providing clear warnings if pixel bits are altered.
5. **Quality Metrics Engine**: Calculates MSE, PSNR (dB), and SSIM metrics between cover and stego images.
6. **Steganalysis Module**: Performs Chi-Square ($\chi^2$) statistical tests on pixel pairs, Shannon entropy computation, LSB zero/one ratio, neighbour correlation, and a 0–100 suspicion score.
7. **Zero Data Retention**: Secret payloads and passwords are processed strictly in-memory (`io.BytesIO`) and are never written to disk or database.

---

## Setup & Running Instructions

### 1. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 2. Run Automated Tests
```bash
python -m pytest
```

### 3. Run the Flask Web Application
```bash
python app.py
```
Access the application in your browser at `http://127.0.0.1:5000`.
