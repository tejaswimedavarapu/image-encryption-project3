#!/usr/bin/env python3
"""
imcrypt - A secure image encryption CLI tool
Encrypts images so only holders of a secure key can decrypt them.
Supports multiple ciphers/modes and random IVs for each image.

Author: theninza <https://theninza.me>
Modified for Python with cryptography library
"""

import click
import sys
from pathlib import Path

from utils.crypto_engine import CryptoEngine, SUPPORTED_MODES
from utils.image_handler import ImageHandler
from utils.key_manager import KeyManager
from utils.ui import welcome, success, error, warning, info, spinner


@click.group(invoke_without_command=True)
@click.option('--version', '-v', is_flag=True, help='Print CLI version')
@click.pass_context
def cli(ctx, version):
    """imcrypt - Secure Image Encryption CLI"""
    if version:
        info("imcrypt v2.0.0 (Python Edition)")
        return

    if ctx.invoked_subcommand is None:
        welcome()
        click.echo(ctx.get_help())


@cli.command()
@click.option('--input', '-i', 'input_path', required=True, type=click.Path(exists=True), 
              help='Input image file to encrypt')
@click.option('--output', '-o', 'output_path', required=False, type=click.Path(),
              help='Output encrypted image file')
@click.option('--key-out', '-k', 'key_output', required=False, type=click.Path(),
              help='Output key file path')
@click.option('--cipher', '-c', default='AES', type=click.Choice(list(SUPPORTED_MODES.keys())),
              help='Cipher algorithm to use')
@click.option('--mode', '-m', default='GCM', type=click.Choice(['CBC', 'GCM', 'CTR']),
              help='Mode of operation')
@click.option('--key-size', '-s', default=256, type=click.Choice([128, 192, 256]),
              help='Key size in bits')
def encrypt(input_path, output_path, key_output, cipher, mode, key_size):
    """Encrypt an image file"""
    welcome()

    try:
        # Determine output paths
        input_path = Path(input_path)
        if not output_path:
            output_path = input_path.parent / f"{input_path.stem}_encrypted{input_path.suffix}"
        else:
            output_path = Path(output_path)

        if not key_output:
            key_output = input_path.parent / f"{input_path.stem}_key.json"
        else:
            key_output = Path(key_output)

        # Check if output files already exist
        if output_path.exists():
            warning(f"Output file already exists: {output_path}")
            if not click.confirm("Overwrite?"):
                info("Encryption cancelled")
                return

        if key_output.exists():
            warning(f"Key file already exists: {key_output}")
            if not click.confirm("Overwrite?"):
                info("Encryption cancelled")
                return

        # Read image
        with spinner("Reading image...") as s:
            image_handler = ImageHandler()
            image_data, metadata = image_handler.read_image(str(input_path))
            s.ok("Image read successfully")

        # Initialize crypto engine
        with spinner(f"Initializing {cipher}-{mode}-{key_size}...") as s:
            crypto = CryptoEngine(cipher=cipher, mode=mode, key_size=key_size)
            s.ok(f"Crypto engine initialized ({cipher}-{mode}-{key_size})")

        # Generate key and encrypt
        with spinner("Generating secure key...") as s:
            key = crypto.generate_key()
            s.ok("Key generated successfully")

        with spinner("Encrypting image data...") as s:
            encrypted_data, iv, tag = crypto.encrypt(image_data)
            s.ok("Image encrypted successfully")

        # Save encrypted image
        with spinner("Saving encrypted image...") as s:
            image_handler.write_encrypted(str(output_path), encrypted_data, metadata)
            s.ok("Encrypted image saved")

        # Save key
        with spinner("Saving key...") as s:
            key_manager = KeyManager()
            key_manager.save_key(
                str(key_output),
                key=key,
                iv=iv,
                tag=tag,
                cipher=cipher,
                mode=mode,
                key_size=key_size,
                original_metadata=metadata
            )
            s.ok("Key saved successfully")

        success("Encryption Complete", f"""
Encrypted Image: {output_path}
Key File:        {key_output}
Algorithm:       {cipher}-{mode}-{key_size}
IV Length:       {len(iv)} bytes
""")

        click.echo()
        info("Keep your key file safe - without it, decryption is impossible!")

    except Exception as e:
        error("Encryption failed", str(e))
        sys.exit(1)


@cli.command()
@click.option('--input', '-i', 'input_path', required=True, type=click.Path(exists=True),
              help='Encrypted image file to decrypt')
@click.option('--key', '-k', 'key_path', required=True, type=click.Path(exists=True),
              help='Key file for decryption')
@click.option('--output', '-o', 'output_path', required=False, type=click.Path(),
              help='Output decrypted image file')
def decrypt(input_path, key_path, output_path):
    """Decrypt an image file using its key"""
    welcome()

    try:
        input_path = Path(input_path)
        key_path = Path(key_path)

        if not output_path:
            output_path = input_path.parent / f"{input_path.stem}_decrypted{input_path.suffix}"
        else:
            output_path = Path(output_path)

        if output_path.exists():
            warning(f"Output file already exists: {output_path}")
            if not click.confirm("Overwrite?"):
                info("Decryption cancelled")
                return

        # Load key
        with spinner("Loading key...") as s:
            key_manager = KeyManager()
            key_data = key_manager.load_key(str(key_path))
            s.ok("Key loaded successfully")

        # Initialize crypto engine with stored parameters
        with spinner("Initializing decryption engine...") as s:
            crypto = CryptoEngine(
                cipher=key_data['cipher'],
                mode=key_data['mode'],
                key_size=key_data['key_size']
            )
            s.ok("Decryption engine ready")

        # Read encrypted image
        with spinner("Reading encrypted image...") as s:
            image_handler = ImageHandler()
            encrypted_data, _ = image_handler.read_encrypted(str(input_path))
            s.ok("Encrypted image loaded")

        # Decrypt
        with spinner("Decrypting...") as s:
            decrypted_data = crypto.decrypt(
                encrypted_data,
                key=key_data['key'],
                iv=key_data['iv'],
                tag=key_data.get('tag')
            )
            s.ok("Decryption successful")

        # Save decrypted image
        with spinner("Saving decrypted image...") as s:
            image_handler.write_image(
                str(output_path),
                decrypted_data,
                key_data['original_metadata']
            )
            s.ok("Image saved successfully")

        success("Decryption Complete", f"""
Decrypted Image: {output_path}
Original Format: {key_data['original_metadata']['format']}
Algorithm Used:  {key_data['cipher']}-{key_data['mode']}-{key_data['key_size']}
""")

    except Exception as e:
        error("Decryption failed", str(e))
        sys.exit(1)


@cli.command()
def list_modes():
    """List available cipher modes and their tradeoffs"""
    welcome()

    info("Available Cipher Modes:")
    click.echo()

    modes_info = {
        'GCM': {
            'full_name': 'Galois/Counter Mode',
            'type': 'Authenticated Encryption',
            'pros': ['Provides both confidentiality AND authenticity', 'Parallelizable', 'Widely recommended'],
            'cons': ['Slightly slower than CTR', 'Tag verification required'],
            'best_for': 'Most use cases - provides authenticated encryption'
        },
        'CBC': {
            'full_name': 'Cipher Block Chaining',
            'type': 'Confidentiality Only',
            'pros': ['Well-understood, widely supported', 'Sequential processing'],
            'cons': ['No authentication (vulnerable to tampering)', 'Requires padding', 'Not parallelizable for encryption'],
            'best_for': 'Legacy compatibility only - not recommended for new systems'
        },
        'CTR': {
            'full_name': 'Counter Mode',
            'type': 'Confidentiality Only',
            'pros': ['Parallelizable', 'No padding needed', 'Fast'],
            'cons': ['No authentication', 'Nonce reuse is catastrophic'],
            'best_for': 'High-performance needs where authentication is handled separately'
        }
    }

    for mode, details in modes_info.items():
        click.echo(click.style(f"  {mode} - {details['full_name']}", fg='cyan', bold=True))
        click.echo(f"  Type: {details['type']}")
        click.echo(f"  Pros: {', '.join(details['pros'])}")
        click.echo(f"  Cons: {', '.join(details['cons'])}")
        click.echo(f"  Best for: {details['best_for']}")
        click.echo()

    info("Recommendation: Use GCM mode for most applications. It provides authenticated encryption,")
    info("meaning an attacker cannot modify the ciphertext without detection.")


if __name__ == '__main__':
    cli()
