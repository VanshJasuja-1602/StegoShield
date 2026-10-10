import os

class Config:
    SECRET_KEY = os.urandom(32)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload size
    
    # StegoShield Cryptographic Protocol Constants
    MAGIC_BYTES = b"STEGO"
    PROTOCOL_VERSION = 1
    PBKDF2_ITERATIONS = 100_000
    SALT_SIZE = 16
    NONCE_SIZE = 12
    TAG_SIZE = 16
    HEADER_SIZE = 39  # Magic(5) + Ver(1) + LSB(1) + Salt(16) + Nonce(12) + Length(4)
