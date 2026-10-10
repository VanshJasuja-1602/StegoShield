import pytest
from encryption import encrypt_message, decrypt_message, EncryptionError

def test_encrypt_decrypt_round_trip():
    """1. Test encrypt/decrypt round trip."""
    secret = "StegoShield Top Secret Message 2026!"
    password = "SuperStrongPassword123"

    encrypted_payload = encrypt_message(secret, password)
    assert isinstance(encrypted_payload, bytes)
    assert len(encrypted_payload) > 28  # 16 salt + 12 nonce + payload

    decrypted_secret = decrypt_message(encrypted_payload, password)
    assert decrypted_secret == secret

def test_wrong_password_fails_safely():
    """2. Test wrong password raises EncryptionError safely."""
    secret = "Confidential Data"
    correct_password = "CorrectPassword"
    wrong_password = "IncorrectPassword"

    encrypted_payload = encrypt_message(secret, correct_password)

    with pytest.raises(EncryptionError) as exc_info:
        decrypt_message(encrypted_payload, wrong_password)
    assert "Decryption failed: Incorrect password or corrupted payload data." in str(exc_info.value)

def test_corrupted_ciphertext_fails_integrity():
    """3. Test corrupted ciphertext fails AEAD integrity verification."""
    secret = "Message to tamper with"
    password = "Password123"

    encrypted_payload = bytearray(encrypt_message(secret, password))
    # Flip bits in the ciphertext portion
    encrypted_payload[-3] ^= 0xFF

    with pytest.raises(EncryptionError) as exc_info:
        decrypt_message(bytes(encrypted_payload), password)
    assert "Decryption failed: Incorrect password or corrupted payload data." in str(exc_info.value)

def test_empty_message_raises_error():
    """4. Test empty message handling."""
    password = "Password123"

    with pytest.raises(EncryptionError) as exc_info:
        encrypt_message("", password)
    assert "Secret message cannot be empty." in str(exc_info.value)

def test_unicode_message_round_trip():
    """5. Test Unicode message round trip (emojis, international characters, special symbols)."""
    unicode_secret = "🔐 StegoShield Security Test: こんにちは 🚀 Shielded Payload! 🛡️"
    password = "UnicodePassword🔑"

    encrypted_payload = encrypt_message(unicode_secret, password)
    decrypted_secret = decrypt_message(encrypted_payload, password)

    assert decrypted_secret == unicode_secret
