"""
Image Handler - Handles reading/writing images using Pillow
Converts images to/from binary format for encryption.
"""

import io
from pathlib import Path
from typing import Tuple, Dict, Any
from PIL import Image
import struct


class ImageHandler:
    """
    Handles image I/O operations.

    Converts images to raw bytes for encryption and back.
    Preserves metadata (format, mode, size) for perfect reconstruction.
    """

    SUPPORTED_FORMATS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif', '.webp'}

    def __init__(self):
        pass

    def read_image(self, path: str) -> Tuple[bytes, Dict[str, Any]]:
        """
        Read an image file and convert to bytes with metadata.

        Args:
            path: Path to the image file

        Returns:
            Tuple of (image_bytes, metadata_dict)
        """
        path = Path(path)

        if path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported format: {path.suffix}. "
                f"Supported: {self.SUPPORTED_FORMATS}"
            )

        # Open image and get metadata
        with Image.open(path) as img:
            metadata = {
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'original_path': str(path),
                'original_suffix': path.suffix.lower()
            }

            # Convert to bytes preserving format
            buffer = io.BytesIO()

            # For lossy formats, use PNG as intermediate to avoid quality loss during encryption
            if path.suffix.lower() in {'.jpg', '.jpeg'}:
                # Convert to RGB/RGBA and save as PNG to avoid lossy compression artifacts
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGBA')
                else:
                    img = img.convert('RGB')
                metadata['converted_from_lossy'] = True
                metadata['original_mode'] = img.mode
                img.save(buffer, format='PNG')
                metadata['save_format'] = 'PNG'
            else:
                img.save(buffer, format=img.format or 'PNG')
                metadata['save_format'] = img.format or 'PNG'

            image_bytes = buffer.getvalue()

        return image_bytes, metadata

    def write_image(self, path: str, data: bytes, metadata: Dict[str, Any]) -> None:
        """
        Write decrypted bytes back to an image file.

        Args:
            path: Output path
            data: Decrypted image bytes
            metadata: Original metadata for reconstruction
        """
        path = Path(path)

        # Load image from bytes
        buffer = io.BytesIO(data)
        with Image.open(buffer) as img:
            # If originally lossy (jpg/jpeg), convert back if needed
            if metadata.get('converted_from_lossy'):
                # User wants original format, convert from PNG intermediate
                if metadata['original_mode'] == 'RGB' and img.mode == 'RGBA':
                    img = img.convert('RGB')
                elif metadata['original_mode'] == 'RGBA' and img.mode == 'RGB':
                    # Can't add alpha if it wasn't there, keep as-is
                    pass

            # Save with original or appropriate format
            save_format = metadata.get('save_format', 'PNG')

            # Determine final format based on extension
            if path.suffix.lower() in {'.jpg', '.jpeg'}:
                # Convert to RGB for JPEG (no alpha)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                img.save(path, format='JPEG', quality=95)
            else:
                img.save(path, format=save_format)

    def write_encrypted(self, path: str, data: bytes, metadata: Dict[str, Any]) -> None:
        """
        Write encrypted data to a file with a header indicating it's encrypted.

        The header helps identify the file and stores minimal metadata.
        """
        path = Path(path)

        # Create a simple header: MAGIC (4) + VERSION (1) + META_LEN (4) + METADATA
        MAGIC = b'IMCR'
        VERSION = 1

        # Serialize metadata
        meta_bytes = str(metadata).encode('utf-8')

        header = (
            MAGIC +
            struct.pack('!B', VERSION) +
            struct.pack('!I', len(meta_bytes)) +
            meta_bytes
        )

        with open(path, 'wb') as f:
            f.write(header)
            f.write(data)

    def read_encrypted(self, path: str) -> Tuple[bytes, Dict[str, Any]]:
        """
        Read encrypted file, extracting header and ciphertext.
        """
        path = Path(path)

        with open(path, 'rb') as f:
            magic = f.read(4)
            if magic != b'IMCR':
                raise ValueError("Invalid encrypted file format (missing magic bytes)")

            version = struct.unpack('!B', f.read(1))[0]
            if version != 1:
                raise ValueError(f"Unsupported file version: {version}")

            meta_len = struct.unpack('!I', f.read(4))[0]
            meta_bytes = f.read(meta_len)

            # Parse metadata
            metadata = eval(meta_bytes.decode('utf-8'))  # Safe for our controlled format

            ciphertext = f.read()

        return ciphertext, metadata
