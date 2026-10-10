import io
import json
import base64
import pytest
from PIL import Image
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def create_image_file(width=100, height=100, color=(100, 150, 200)):
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def test_all_8_page_routes(client):
    """Test all 8 dashboard pages render successfully (HTTP 200)."""
    routes = [
        '/',
        '/encode',
        '/decode',
        '/analyze',
        '/tamper-detection',
        '/steganalysis',
        '/history',
        '/about'
    ]
    for route in routes:
        response = client.get(route)
        assert response.status_code == 200, f"Failed on route {route}"

def test_tamper_simulation_api(client):
    """Test /api/tamper/simulate endpoint."""
    img_buf = create_image_file(80, 80)
    data = {
        'stego_image': (img_buf, 'test.png'),
        'action': 'modify_pixel'
    }
    rv = client.post('/api/tamper/simulate', data=data, content_type='multipart/form-data')
    res = json.loads(rv.data)

    assert rv.status_code == 200
    assert res['success'] is True
    assert 'manipulated_image_b64' in res
    assert res['action'] == 'modify_pixel'

def test_integrated_encode_and_decode_flow(client):
    """
    Test Integrated Flow:
    Secret Message -> Password Encryption -> Encrypted Payload -> Metadata Header -> LSB Embedding -> Stego PNG
    Stego PNG -> Extract Payload -> Validate Payload -> Password Decryption -> Secret Message
    """
    cover_buf = create_image_file(120, 120)
    secret_text = "Integrate Encryption and Steganography Test Secret!"
    password = "IntegratedSecretPassword2026"

    # Step 1: Encode Route
    embed_data = {
        'cover_image': (cover_buf, 'cover.png'),
        'secret_text': secret_text,
        'password': password,
        'lsb_count': '1'
    }
    embed_res = client.post('/api/embed', data=embed_data, content_type='multipart/form-data')
    embed_json = json.loads(embed_res.data)

    assert embed_res.status_code == 200
    assert embed_json['success'] is True
    assert 'stego_image_b64' in embed_json
    assert embed_json['metrics']['psnr'] > 40.0

    stego_b64_str = embed_json['stego_image_b64'].split(',')[1]
    stego_raw = base64.b64decode(stego_b64_str)
    stego_buf = io.BytesIO(stego_raw)

    # Step 2: Decode Route
    extract_data = {
        'stego_image': (stego_buf, 'stego.png'),
        'password': password
    }
    extract_res = client.post('/api/extract', data=extract_data, content_type='multipart/form-data')
    extract_json = json.loads(extract_res.data)

    assert extract_res.status_code == 200
    assert extract_json['success'] is True
    assert extract_json['secret_message'] == secret_text
    assert extract_json['tampered'] is False
    assert extract_json['status'] == "Likely Unmodified"

def test_integrated_wrong_password_meaningful_error(client):
    """Test wrong password returns meaningful error message."""
    cover_buf = create_image_file(100, 100)
    embed_data = {
        'cover_image': (cover_buf, 'cover.png'),
        'secret_text': "Secret payload",
        'password': "RightPassword123",
        'lsb_count': '1'
    }
    embed_res = client.post('/api/embed', data=embed_data, content_type='multipart/form-data')
    embed_json = json.loads(embed_res.data)

    stego_b64_str = embed_json['stego_image_b64'].split(',')[1]
    stego_buf = io.BytesIO(base64.b64decode(stego_b64_str))

    extract_data = {
        'stego_image': (stego_buf, 'stego.png'),
        'password': "WrongPassword456"
    }
    extract_res = client.post('/api/extract', data=extract_data, content_type='multipart/form-data')
    extract_json = json.loads(extract_res.data)

    assert extract_res.status_code == 400
    assert extract_json['success'] is False
    assert extract_json['tampered'] is True
    assert "Authentication Tag Failure" in extract_json['error'] or "Incorrect password" in extract_json['error']

def test_non_stego_image_extraction_error(client):
    """Test extracting from clean non-stego image returns header validation error."""
    clean_buf = create_image_file(100, 100)
    extract_data = {
        'stego_image': (clean_buf, 'clean.png'),
        'password': "AnyPassword123"
    }
    extract_res = client.post('/api/extract', data=extract_data, content_type='multipart/form-data')
    extract_json = json.loads(extract_res.data)

    assert extract_res.status_code == 400
    assert extract_json['success'] is False
    assert "Header Validation Error" in extract_json['error'] or "Header check failed" in extract_json['error']
