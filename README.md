# image-encryption-project3
# imcrypt v2.0.0 (Python Edition)

A secure CLI that encrypts and decrypts images using industry-standard cryptography. Only holders of the secure key can decrypt them. Supports multiple ciphers, modes of operation, and generates random IVs for each encryption.

![Python](https://img.shields.io/badge/Python-3.8+-05122A?style=for-the-badge&logo=python)
![Cryptography](https://img.shields.io/badge/cryptography-library-green?style=for-the-badge)

## Tech Stack

- **Python 3.8+**
- **cryptography** - Industry-standard cryptographic library
- **Pillow (PIL)** - Image processing
- **Click** - CLI framework

## Features

- **Multiple Ciphers**: AES and ChaCha20-Poly1305
- **Multiple Modes**: CBC, GCM, CTR (for AES)
- **Authenticated Encryption**: GCM and ChaCha20-Poly1305 provide both confidentiality AND integrity
- **Random IVs**: Each encryption uses a unique random IV/nonce
- **Secure Key Generation**: Uses `secrets.token_bytes()` for CSPRNG
- **Key Size Options**: 128, 192, 256-bit keys for AES
- **Format Preservation**: Maintains image quality (handles lossy formats intelligently)

## Installation

```bash
# Clone or download the repository
cd imcrypt-python

# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

## Usage

### Encrypt an image

```bash
# Basic encryption (AES-256-GCM - recommended)
python imcrypt.py encrypt -i myImage.png

# Specify output files
python imcrypt.py encrypt -i myImage.png -o encrypted.png -k myKey.json

# Use ChaCha20-Poly1305
python imcrypt.py encrypt -i myImage.png -c ChaCha20

# Use AES-128-CBC (legacy compatibility)
python imcrypt.py encrypt -i myImage.png -c AES -m CBC -s 128
```

### Decrypt an image

```bash
# Basic decryption
python imcrypt.py decrypt -i encrypted.png -k myKey.json

# Specify output
python imcrypt.py decrypt -i encrypted.png -k myKey.json -o decrypted.png
```

### List available modes

```bash
python imcrypt.py list-modes
```

## Command Reference

| Command | Description |
|---------|-------------|
| `encrypt` | Encrypt an image file |
| `decrypt` | Decrypt an image using its key |
| `list-modes` | Show cipher modes and their tradeoffs |

### Encrypt Options

| Option | Short | Description |
|--------|-------|-------------|
| `--input` | `-i` | Input image file (required) |
| `--output` | `-o` | Output encrypted file |
| `--key-out` | `-k` | Output key file |
| `--cipher` | `-c` | Cipher: `AES` or `ChaCha20` (default: AES) |
| `--mode` | `-m` | Mode: `CBC`, `GCM`, `CTR` (default: GCM) |
| `--key-size` | `-s` | Key size: `128`, `192`, `256` (default: 256) |

### Decrypt Options

| Option | Short | Description |
|--------|-------|-------------|
| `--input` | `-i` | Encrypted image file (required) |
| `--key` | `-k` | Key file (required) |
| `--output` | `-o` | Output decrypted file |

## Mode Tradeoffs

| Mode | Authentication | Parallelizable | Padding | Recommendation |
|------|---------------|----------------|---------|----------------|
| **GCM** | Yes | Yes | No | **Recommended** - Best balance of security and performance |
| **CTR** | No | Yes | No | Fast, but no integrity protection |
| **CBC** | No | No | Yes | Legacy only - slower, no authentication |

## Security Notes

1. **Keep your key file secure**: Anyone with the key file can decrypt your image
2. **Key file permissions**: Set to 600 (owner read/write only)
3. **Never reuse IVs**: Each encryption generates a unique random IV
4. **Authenticated modes**: Use GCM or ChaCha20-Poly1305 for tamper detection
5. **Lossy formats**: JPEG images are converted to PNG during encryption to avoid compression artifacts, then converted back on decryption

## Examples

### Encrypt with AES-256-GCM
```bash
$ python imcrypt.py encrypt -i photo.jpg -o secret.jpg -k key.json

✔ Encryption Complete
Encrypted Image: secret.jpg
Key File:        key.json
Algorithm:       AES-GCM-256
IV Length:       12 bytes
```

### Decrypt with key
```bash
$ python imcrypt.py decrypt -i secret.jpg -k key.json -o restored.jpg

✔ Decryption Complete
Decrypted Image: restored.jpg
Original Format: JPEG
Algorithm Used:  AES-GCM-256
```

## Learning Outcomes

This project demonstrates:
- **Binary data encryption**: Encrypting arbitrary binary data (images)
- **Secure key handling**: Using CSPRNGs, proper key storage, restrictive permissions
- **Mode of operation tradeoffs**: Understanding when to use GCM vs CTR vs CBC
- **Authenticated encryption**: Why confidentiality alone is not enough
- **IV management**: Why random IVs matter and how to handle them

## License

MIT
