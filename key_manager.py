"""
Key Manager - Securely handles key storage and retrieval
Keys are stored in JSON format with all necessary parameters.
"""

import json
import base64
import os
from pathlib import Path
from typing import Dict, Any


class KeyManager:
    """
    Manages encryption keys securely.

    Keys are stored with:
    - Base64-encoded key material
    - IV/nonce used
    - Cipher and mode information
    - Original image metadata
    - Authentication tag (for authenticated modes)

    The key file should be kept secure - anyone with access can decrypt!
    """

    def __init__(self):
        pass

    def save_key(self, path: str, key: bytes, iv: bytes, tag: bytes,
                 cipher: str, mode: str, key_size: int,
                 original_metadata: Dict[str, Any]) -> None:
        """
        Save encryption key and parameters to a file.

        Args:
            path: Path to save the key file
            key: The encryption key
            iv: The initialization vector/nonce
            tag: Authentication tag (if applicable)
            cipher: Cipher algorithm used
            mode: Mode of operation used
            key_size: Key size in bits
            original_metadata: Original image metadata for reconstruction
        """
        key_data = {
            'version': 1,
            'cipher': cipher,
            'mode': mode,
            'key_size': key_size,
            'key': base64.b64encode(key).decode('ascii'),
            'iv': base64.b64encode(iv).decode('ascii'),
            'tag': base64.b64encode(tag).decode('ascii') if tag else None,
            'original_metadata': original_metadata,
            'warning': 'KEEP THIS FILE SECURE - anyone with access can decrypt your image!'
        }

        path = Path(path)

        # Ensure .json extension
        if path.suffix != '.json':
            path = path.with_suffix('.json')

        with open(path, 'w') as f:
            json.dump(key_data, f, indent=2)

        # Set restrictive permissions (owner read/write only)
        os.chmod(path, 0o600)

    def load_key(self, path: str) -> Dict[str, Any]:
        """
        Load key and parameters from a file.

        Returns:
            Dictionary with decoded key material
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Key file not found: {path}")

        with open(path, 'r') as f:
            key_data = json.load(f)

        # Validate version
        if key_data.get('version') != 1:
            raise ValueError(f"Unsupported key file version: {key_data.get('version')}")

        # Decode base64 fields
        try:
            key_data['key'] = base64.b64decode(key_data['key'])
            key_data['iv'] = base64.b64decode(key_data['iv'])
            if key_data.get('tag'):
                key_data['tag'] = base64.b64decode(key_data['tag'])
        except Exception as e:
            raise ValueError(f"Invalid key file format: {e}")

        return key_data

    def validate_key(self, key_data: Dict[str, Any]) -> bool:
        """Validate that key data contains all required fields."""
        required = ['key', 'iv', 'cipher', 'mode', 'key_size', 'original_metadata']
        return all(field in key_data for field in required)
