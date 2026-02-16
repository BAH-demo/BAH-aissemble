"""
STIG V-220633 / NIST SC-28: Encryption at Rest
AES-256 encryption helpers for sensitive configuration values.
"""

import os
import base64
import hashlib
import logging
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    _HAS_CRYPTOGRAPHY = True
except ImportError:
    _HAS_CRYPTOGRAPHY = False


AES_KEY_SIZE = 32
AES_NONCE_SIZE = 12


class EncryptionHelper:
    """AES-256-GCM encryption for sensitive data at rest per STIG V-220633."""

    def __init__(self, key: Optional[bytes] = None, key_env_var: str = "AISSEMBLE_ENCRYPTION_KEY"):
        if key:
            self._key = self._validate_key(key)
        else:
            env_key = os.environ.get(key_env_var)
            if env_key:
                self._key = self._validate_key(base64.b64decode(env_key))
            else:
                logger.warning(
                    "No encryption key provided. Set %s environment variable "
                    "or pass key directly.", key_env_var,
                )
                self._key = None

    @staticmethod
    def _validate_key(key: bytes) -> bytes:
        if len(key) != AES_KEY_SIZE:
            raise ValueError(f"Encryption key must be {AES_KEY_SIZE} bytes (AES-256)")
        return key

    @staticmethod
    def generate_key() -> bytes:
        return os.urandom(AES_KEY_SIZE)

    @staticmethod
    def key_to_base64(key: bytes) -> str:
        return base64.b64encode(key).decode("utf-8")

    @staticmethod
    def key_from_passphrase(passphrase: str, salt: Optional[bytes] = None) -> bytes:
        if salt is None:
            salt = os.urandom(16)
        derived = hashlib.pbkdf2_hmac("sha256", passphrase.encode("utf-8"), salt, 600000, dklen=AES_KEY_SIZE)
        return derived

    def encrypt(self, plaintext: str) -> Optional[str]:
        if not self._key:
            logger.error("Cannot encrypt: no encryption key configured")
            return None
        if not _HAS_CRYPTOGRAPHY:
            logger.error("Cannot encrypt: cryptography library not installed")
            return None
        try:
            nonce = os.urandom(AES_NONCE_SIZE)
            aesgcm = AESGCM(self._key)
            ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
            combined = nonce + ciphertext
            return base64.b64encode(combined).decode("utf-8")
        except Exception:
            logger.error("Encryption failed")
            return None

    def decrypt(self, encrypted_data: str) -> Optional[str]:
        if not self._key:
            logger.error("Cannot decrypt: no encryption key configured")
            return None
        if not _HAS_CRYPTOGRAPHY:
            logger.error("Cannot decrypt: cryptography library not installed")
            return None
        try:
            raw = base64.b64decode(encrypted_data)
            nonce = raw[:AES_NONCE_SIZE]
            ciphertext = raw[AES_NONCE_SIZE:]
            aesgcm = AESGCM(self._key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode("utf-8")
        except Exception:
            logger.error("Decryption failed")
            return None
