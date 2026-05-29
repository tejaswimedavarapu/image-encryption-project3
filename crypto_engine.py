"""
Crypto Engine - Handles encryption/decryption with multiple cipher modes
Supports AES and ChaCha20 with CBC, GCM, and CTR modes.
"""

import os
import secrets
from typing import Tuple, Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag


SUPPORTED_MODES = {
    'AES': {
        'CBC': modes.CBC,
        'GCM': modes.GCM,
        'CTR': modes.CTR
    },
    'ChaCha20': {
        'GCM': None  # ChaCha20Poly1305 is AEAD by design
    }
}


class CryptoEngine:
    """
    Secure cryptographic engine for image encryption.

    Supports:
    - AES-128/192/256 with CBC, GCM, CTR modes
    - ChaCha20-Poly1305 (always authenticated)

    Each encryption generates a random IV/nonce.
    """

    def __init__(self, cipher: str = 'AES', mode: str = 'GCM', key_size: int = 256):
        """
        Initialize the crypto engine.

        Args:
            cipher: 'AES' or 'ChaCha20'
            mode: 'CBC', 'GCM', or 'CTR'
            key_size: 128, 192, or 256 (ignored for ChaCha20 which always uses 256)
        """
        self.cipher = cipher.upper()
        self.mode = mode.upper()
        self.key_size = key_size

        # Validate cipher/mode combination
        if self.cipher not in SUPPORTED_MODES:
            raise ValueError(f"Unsupported cipher: {cipher}. Use: {list(SUPPORTED_MODES.keys())}")

        if self.mode not in SUPPORTED_MODES[self.cipher]:
            raise ValueError(
                f"Mode {mode} not supported for {cipher}. "
                f"Available: {list(SUPPORTED_MODES[self.cipher].keys())}"
            )

        # Set key size
        if self.cipher == 'AES':
            if key_size not in [128, 192, 256]:
                raise ValueError("AES key size must be 128, 192, or 256 bits")
            self.key_length = key_size // 8
        else:  # ChaCha20
            self.key_length = 32  # ChaCha20 always uses 256-bit keys

        # Set IV/nonce length
        if self.cipher == 'AES':
            self.iv_length = 12 if self.mode == 'GCM' else 16  # GCM uses 96-bit nonce
        else:
            self.iv_length = 12  # ChaCha20 uses 96-bit nonce

    def generate_key(self) -> bytes:
        """Generate a cryptographically secure random key."""
        return secrets.token_bytes(self.key_length)

    def generate_iv(self) -> bytes:
        """Generate a random IV/nonce. Never reuse IVs with the same key!"""
        return secrets.token_bytes(self.iv_length)

    def encrypt(self, plaintext: bytes) -> Tuple[bytes, bytes, Optional[bytes]]:
        """
        Encrypt data with a randomly generated key and IV.

        Args:
            plaintext: The data to encrypt

        Returns:
            Tuple of (ciphertext, iv, tag)
            - tag is None for non-authenticated modes (CBC, CTR)
        """
        key = self.generate_key()
        iv = self.generate_iv()

        if self.cipher == 'AES':
            if self.mode == 'GCM':
                # AES-GCM: Authenticated encryption
                aesgcm = AESGCM(key)
                ciphertext = aesgcm.encrypt(iv, plaintext, None)
                # ciphertext includes tag appended (last 16 bytes)
                tag = None  # Tag is embedded in ciphertext for AESGCM

            elif self.mode == 'CBC':
                # AES-CBC: Requires padding
                from cryptography.hazmat.primitives import padding
                padder = padding.PKCS7(128).padder()
                padded_data = padder.update(plaintext) + padder.finalize()

                cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
                encryptor = cipher.encryptor()
                ciphertext = encryptor.update(padded_data) + encryptor.finalize()
                tag = None

            elif self.mode == 'CTR':
                # AES-CTR: No padding needed, acts like stream cipher
                cipher = Cipher(algorithms.AES(key), modes.CTR(iv), backend=default_backend())
                encryptor = cipher.encryptor()
                ciphertext = encryptor.update(plaintext) + encryptor.finalize()
                tag = None

        elif self.cipher == 'ChaCha20':
            # ChaCha20-Poly1305: Always authenticated
            chacha = ChaCha20Poly1305(key)
            ciphertext = chacha.encrypt(iv, plaintext, None)
            tag = None  # Tag is embedded

        return ciphertext, iv, tag

    def decrypt(self, ciphertext: bytes, key: bytes, iv: bytes, 
                tag: Optional[bytes] = None) -> bytes:
        """
        Decrypt data.

        Args:
            ciphertext: The encrypted data
            key: The encryption key
            iv: The initialization vector/nonce
            tag: Authentication tag (for GCM mode, if separate)

        Returns:
            The decrypted plaintext

        Raises:
            InvalidTag: If authentication fails (for authenticated modes)
            ValueError: If decryption parameters are invalid
        """
        if len(key) != self.key_length:
            raise ValueError(f"Invalid key length: expected {self.key_length}, got {len(key)}")

        if len(iv) != self.iv_length:
            raise ValueError(f"Invalid IV length: expected {self.iv_length}, got {len(iv)}")

        try:
            if self.cipher == 'AES':
                if self.mode == 'GCM':
                    aesgcm = AESGCM(key)
                    plaintext = aesgcm.decrypt(iv, ciphertext, None)

                elif self.mode == 'CBC':
                    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
                    decryptor = cipher.decryptor()
                    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

                    # Remove padding
                    from cryptography.hazmat.primitives import padding
                    unpadder = padding.PKCS7(128).unpadder()
                    plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()

                elif self.mode == 'CTR':
                    cipher = Cipher(algorithms.AES(key), modes.CTR(iv), backend=default_backend())
                    decryptor = cipher.decryptor()
                    plaintext = decryptor.update(ciphertext) + decryptor.finalize()

            elif self.cipher == 'ChaCha20':
                chacha = ChaCha20Poly1305(key)
                plaintext = chacha.decrypt(iv, ciphertext, None)

        except InvalidTag:
            raise InvalidTag("Authentication failed! The ciphertext may have been tampered with.")

        return plaintext

    def get_info(self) -> dict:
        """Get information about the current cipher configuration."""
        return {
            'cipher': self.cipher,
            'mode': self.mode,
            'key_size_bits': self.key_length * 8,
            'key_size_bytes': self.key_length,
            'iv_length_bytes': self.iv_length,
            'authenticated': self.mode == 'GCM' or self.cipher == 'ChaCha20'
        }
