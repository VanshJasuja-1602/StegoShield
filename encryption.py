import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

class EncryptionError(Exception):
    """Custom exception for encryption and decryption errors."""
    pass

SALT_SIZE = 16
NONCE_SIZE = 12
PBKDF2_ITERATIONS = 100_000

def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit key from a password and salt using PBKDF2HMAC SHA-256."""
    if not password:
        raise EncryptionError("Password cannot be empty.")
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=PBKDF2_ITERATIONS,
    )
    return kdf.derive(password.encode('utf-8'))

def encrypt_message(secret_message: str | bytes, password: str) -> bytes:
    """
    Encrypt a secret message using a password with AES-256-GCM.
    
    Payload Format:
    - Salt (16 bytes)
    - Nonce (12 bytes)
    - Ciphertext + 16-byte Auth Tag (Variable length)
    """
    if secret_message is None:
        raise EncryptionError("Secret message cannot be None.")
        
    if isinstance(secret_message, str):
        if not secret_message:
            raise EncryptionError("Secret message cannot be empty.")
        plaintext_bytes = secret_message.encode('utf-8')
    else:
        if not secret_message:
            raise EncryptionError("Secret message cannot be empty.")
        plaintext_bytes = secret_message

    if not password:
        raise EncryptionError("Password cannot be empty.")

    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(password, salt)

    aesgcm = AESGCM(key)
    ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext_bytes, None)

    return salt + nonce + ciphertext_with_tag

def decrypt_message(payload: bytes, password: str) -> str:
    """
    Decrypt a payload encrypted with encrypt_message using password.
    Returns the original secret message string.
    Raises EncryptionError on wrong password or payload corruption.
    """
    if not payload or not isinstance(payload, (bytes, bytearray)):
        raise EncryptionError("Invalid payload provided.")

    min_length = SALT_SIZE + NONCE_SIZE + 16  # 16 salt + 12 nonce + 16 auth tag
    if len(payload) < min_length:
        raise EncryptionError("Corrupted payload: Payload length is shorter than required header.")

    if not password:
        raise EncryptionError("Password cannot be empty.")

    salt = payload[:SALT_SIZE]
    nonce = payload[SALT_SIZE : SALT_SIZE + NONCE_SIZE]
    ciphertext_with_tag = payload[SALT_SIZE + NONCE_SIZE :]

    key = derive_key(password, salt)
    aesgcm = AESGCM(key)

    try:
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext_with_tag, None)
        return decrypted_bytes.decode('utf-8')
    except InvalidTag:
        raise EncryptionError("Decryption failed: Incorrect password or corrupted payload data.")
    except UnicodeDecodeError:
        raise EncryptionError("Decryption succeeded but failed to decode message as UTF-8.")
