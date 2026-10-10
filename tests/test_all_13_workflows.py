import io
import json
import base64
import pytest
from PIL import Image
import numpy as np
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def create_sample_png_bytes(width=200, height=200):
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    for i in range(height):
        for j in range(width):
            arr[i, j] = [(i * 2) % 256, (j * 3) % 256, (i + j) % 256]
    img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def create_sample_jpeg_bytes(width=100, height=100):
    img = Image.new("RGB", (width, height), (120, 140, 160))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

def test_workflow_1_encode_short_message(client):
    """1. Encode a short message."""
    cover_bytes = create_sample_png_bytes(200, 200)
    data = {
        'cover_image': (io.BytesIO(cover_bytes), 'cover.png'),
        'secret_text': 'Hello StegoShield',
        'password': 'ShortPassword123',
        'lsb_count': '1'
    }
    rv = client.post('/api/embed', data=data, content_type='multipart/form-data')
    res = json.loads(rv.data)

    assert rv.status_code == 200
    assert res['success'] is True
    assert 'stego_image_b64' in res
    assert res['metrics']['psnr'] > 40.0

def test_workflow_2_decode_short_message(client):
    """2. Decode the message."""
    cover_bytes = create_sample_png_bytes(200, 200)
    secret_text = 'Hello StegoShield'
    password = 'ShortPassword123'

    embed_data = {
        'cover_image': (io.BytesIO(cover_bytes), 'cover.png'),
        'secret_text': secret_text,
        'password': password,
        'lsb_count': '1'
    }
    embed_res = client.post('/api/embed', data=embed_data, content_type='multipart/form-data')
    embed_json = json.loads(embed_res.data)

    stego_raw = base64.b64decode(embed_json['stego_image_b64'].split(',')[1])

    extract_data = {
        'stego_image': (io.BytesIO(stego_raw), 'stego.png'),
        'password': password
    }
    extract_res = client.post('/api/extract', data=extract_data, content_type='multipart/form-data')
    extract_json = json.loads(extract_res.data)

    assert extract_res.status_code == 200
    assert extract_json['success'] is True
    assert extract_json['secret_message'] == secret_text
    assert extract_json['status'] == "Likely Unmodified"

def test_workflow_3_encode_long_message(client):
    """3. Encode a long message."""
    cover_bytes = create_sample_png_bytes(200, 200)
    long_msg = "StegoShield Long Payload " * 150  # ~3750 chars
    password = "LongPassword123"

    embed_data = {
        'cover_image': (io.BytesIO(cover_bytes), 'cover.png'),
        'secret_text': long_msg,
        'password': password,
        'lsb_count': '1'
    }
    embed_res = client.post('/api/embed', data=embed_data, content_type='multipart/form-data')
    embed_json = json.loads(embed_res.data)

    assert embed_res.status_code == 200
    assert embed_json['success'] is True

    stego_raw = base64.b64decode(embed_json['stego_image_b64'].split(',')[1])

    extract_data = {
        'stego_image': (io.BytesIO(stego_raw), 'stego.png'),
        'password': password
    }
    extract_res = client.post('/api/extract', data=extract_data, content_type='multipart/form-data')
    extract_json = json.loads(extract_res.data)

    assert extract_res.status_code == 200
    assert extract_json['secret_message'] == long_msg

def test_workflow_4_try_exceeding_image_capacity(client):
    """4. Try exceeding image capacity."""
    tiny_cover_bytes = create_sample_png_bytes(20, 20)  # 20x20 = 150 bytes capacity
    huge_msg = "X" * 10000

    embed_data = {
        'cover_image': (io.BytesIO(tiny_cover_bytes), 'tiny.png'),
        'secret_text': huge_msg,
        'password': 'Pass123',
        'lsb_count': '1'
    }
    embed_res = client.post('/api/embed', data=embed_data, content_type='multipart/form-data')
    embed_json = json.loads(embed_res.data)

    assert embed_res.status_code == 400
    assert embed_json['success'] is False
    assert "Exceeded" in embed_json['error'] or "capacity" in embed_json['error'].lower()

def test_workflow_5_use_wrong_password(client):
    """5. Use a wrong password."""
    cover_bytes = create_sample_png_bytes(100, 100)
    embed_data = {
        'cover_image': (io.BytesIO(cover_bytes), 'cover.png'),
        'secret_text': "Secret payload",
        'password': "RightPassword",
        'lsb_count': '1'
    }
    embed_res = client.post('/api/embed', data=embed_data, content_type='multipart/form-data')
    embed_json = json.loads(embed_res.data)

    stego_raw = base64.b64decode(embed_json['stego_image_b64'].split(',')[1])

    extract_data = {
        'stego_image': (io.BytesIO(stego_raw), 'stego.png'),
        'password': "WrongPassword"
    }
    extract_res = client.post('/api/extract', data=extract_data, content_type='multipart/form-data')
    extract_json = json.loads(extract_res.data)

    assert extract_res.status_code == 400
    assert extract_json['success'] is False
    assert extract_json['tampered'] is True

def test_workflow_6_upload_non_png_file(client):
    """6. Upload a non-PNG file (JPEG)."""
    jpeg_bytes = create_sample_jpeg_bytes(100, 100)
    embed_data = {
        'cover_image': (io.BytesIO(jpeg_bytes), 'cover.jpg'),
        'secret_text': "Test JPEG",
        'password': "Pass123",
        'lsb_count': '1'
    }
    embed_res = client.post('/api/embed', data=embed_data, content_type='multipart/form-data')
    embed_json = json.loads(embed_res.data)

    assert embed_res.status_code == 400
    assert embed_json['success'] is False
    assert "JPEG" in embed_json['error'] or "lossy" in embed_json['error'].lower()

def test_workflow_7_upload_normal_non_stego_image(client):
    """7. Upload a normal non-stego image for extraction."""
    cover_bytes = create_sample_png_bytes(100, 100)
    extract_data = {
        'stego_image': (io.BytesIO(cover_bytes), 'plain.png'),
        'password': "AnyPassword"
    }
    extract_res = client.post('/api/extract', data=extract_data, content_type='multipart/form-data')
    extract_json = json.loads(extract_res.data)

    assert extract_res.status_code == 400
    assert extract_json['success'] is False
    assert "Header Validation Error" in extract_json['error'] or "Header check failed" in extract_json['error']

def test_workflow_8_modify_stego_image(client):
    """8. Modify a stego image (tamper bit flip)."""
    cover_bytes = create_sample_png_bytes(100, 100)
    embed_data = {
        'cover_image': (io.BytesIO(cover_bytes), 'cover.png'),
        'secret_text': "Secret payload to modify",
        'password': "Pass123",
        'lsb_count': '1'
    }
    embed_res = client.post('/api/embed', data=embed_data, content_type='multipart/form-data')
    embed_json = json.loads(embed_res.data)

    stego_raw = base64.b64decode(embed_json['stego_image_b64'].split(',')[1])

    # Modify 1 pixel bit in payload header
    img_pil = Image.open(io.BytesIO(stego_raw)).convert("RGB")
    px = np.array(img_pil, dtype=np.uint8)
    px[0, 15, 0] ^= 1
    mod_buf = io.BytesIO()
    Image.fromarray(px, mode="RGB").save(mod_buf, format="PNG")
    tampered_bytes = mod_buf.getvalue()

    extract_data = {
        'stego_image': (io.BytesIO(tampered_bytes), 'tampered.png'),
        'password': "Pass123"
    }
    extract_res = client.post('/api/extract', data=extract_data, content_type='multipart/form-data')
    extract_json = json.loads(extract_res.data)

    assert extract_res.status_code == 400
    assert extract_json['success'] is False
    assert extract_json['tampered'] is True

def test_workflow_9_test_image_quality_metrics(client):
    """9. Test image-quality metrics."""
    cover_bytes = create_sample_png_bytes(100, 100)
    embed_data = {
        'cover_image': (io.BytesIO(cover_bytes), 'cover.png'),
        'secret_text': "Secret for quality metrics test",
        'password': "Pass123",
        'lsb_count': '1'
    }
    embed_res = client.post('/api/embed', data=embed_data, content_type='multipart/form-data')
    embed_json = json.loads(embed_res.data)

    stego_raw = base64.b64decode(embed_json['stego_image_b64'].split(',')[1])

    compare_data = {
        'cover_image': (io.BytesIO(cover_bytes), 'cover.png'),
        'stego_image': (io.BytesIO(stego_raw), 'stego.png')
    }
    compare_res = client.post('/api/compare', data=compare_data, content_type='multipart/form-data')
    compare_json = json.loads(compare_res.data)

    assert compare_res.status_code == 200
    assert compare_json['success'] is True
    m = compare_json['metrics']
    assert m['psnr'] > 40.0
    assert m['ssim'] > 0.99
    assert 'explanations' in m

def test_workflow_10_test_steganalysis(client):
    """10. Test steganalysis."""
    cover_bytes = create_sample_png_bytes(100, 100)
    analyze_data = {
        'image': (io.BytesIO(cover_bytes), 'image.png')
    }
    analyze_res = client.post('/api/analyze', data=analyze_data, content_type='multipart/form-data')
    analyze_json = json.loads(analyze_res.data)

    assert analyze_res.status_code == 200
    assert analyze_json['success'] is True
    rep = analyze_json['report']
    assert 'suspicion_score' in rep
    assert 'indication' in rep
    assert 'disclaimer' in rep

def test_workflow_11_test_empty_message(client):
    """11. Test empty message."""
    cover_bytes = create_sample_png_bytes(100, 100)
    embed_data = {
        'cover_image': (io.BytesIO(cover_bytes), 'cover.png'),
        'secret_text': "",
        'password': "Pass123",
        'lsb_count': '1'
    }
    embed_res = client.post('/api/embed', data=embed_data, content_type='multipart/form-data')
    embed_json = json.loads(embed_res.data)

    assert embed_res.status_code == 400
    assert embed_json['success'] is False
    assert "empty" in embed_json['error'].lower()

def test_workflow_12_test_special_characters_and_unicode(client):
    """12. Test special characters and Unicode."""
    cover_bytes = create_sample_png_bytes(120, 120)
    unicode_msg = "🔐 StegoShield 2026: こんにちは! Special #$%^&*() World! 🛡️"
    password = "UnicodePassword123"

    embed_data = {
        'cover_image': (io.BytesIO(cover_bytes), 'cover.png'),
        'secret_text': unicode_msg,
        'password': password,
        'lsb_count': '1'
    }
    embed_res = client.post('/api/embed', data=embed_data, content_type='multipart/form-data')
    embed_json = json.loads(embed_res.data)

    assert embed_res.status_code == 200

    stego_raw = base64.b64decode(embed_json['stego_image_b64'].split(',')[1])

    extract_data = {
        'stego_image': (io.BytesIO(stego_raw), 'stego.png'),
        'password': password
    }
    extract_res = client.post('/api/extract', data=extract_data, content_type='multipart/form-data')
    extract_json = json.loads(extract_res.data)

    assert extract_res.status_code == 200
    assert extract_json['secret_message'] == unicode_msg

def test_workflow_13_test_invalid_corrupted_files(client):
    """13. Test invalid/corrupted files."""
    bad_bytes = b"CORRUPTED_NON_IMAGE_BINARY_DATA_12345"
    embed_data = {
        'cover_image': (io.BytesIO(bad_bytes), 'bad.png'),
        'secret_text': "Payload",
        'password': "Pass123",
        'lsb_count': '1'
    }
    embed_res = client.post('/api/embed', data=embed_data, content_type='multipart/form-data')
    embed_json = json.loads(embed_res.data)

    assert embed_res.status_code == 400
    assert embed_json['success'] is False
