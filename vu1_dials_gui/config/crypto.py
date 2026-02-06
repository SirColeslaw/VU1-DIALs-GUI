"""
API key encryption for secure storage at rest.

Provides encryption/decryption of the API key so it is not stored
in plaintext in settings.json. Uses the ``cryptography`` library
(Fernet symmetric encryption) when available, and falls back to
base64 obfuscation otherwise.

The encryption key is stored in a separate file (``.vu1_keyfile``)
next to the settings file. This file should not be shared or
committed to version control.
"""

import base64
import logging
import os
import secrets

logger = logging.getLogger(__name__)

_KEYFILE_NAME: str = ".vu1_keyfile"
_KEY_LENGTH: int = 32  # 256-bit key

# Marker prefixes to distinguish encrypted values in the JSON
_FERNET_PREFIX: str = "enc:fernet:"
_B64_PREFIX: str = "enc:b64:"

# Try to import cryptography for strong encryption
try:
    from cryptography.fernet import Fernet, InvalidToken

    _HAS_FERNET = True
except ImportError:
    _HAS_FERNET = False
    logger.info(
        "cryptography library not installed; "
        "API key will be obfuscated with base64 instead of encrypted. "
        "Install 'cryptography' for stronger protection: pip install cryptography"
    )


def _get_keyfile_path(base_path: str) -> str:
    """Return the full path to the encryption keyfile.

    Args:
        base_path: The application base directory.

    Returns:
        Absolute path to the keyfile.
    """
    return os.path.join(base_path, _KEYFILE_NAME)


def _load_or_create_key(base_path: str) -> bytes:
    """Load the encryption key from disk, or generate a new one.

    If no keyfile exists, a cryptographically random key is generated
    and saved. The keyfile is created with restrictive permissions.

    Args:
        base_path: The application base directory.

    Returns:
        The raw key bytes (32 bytes).
    """
    keyfile = _get_keyfile_path(base_path)

    if os.path.exists(keyfile):
        try:
            with open(keyfile, "rb") as f:
                key = f.read()
            if len(key) >= _KEY_LENGTH:
                return key[:_KEY_LENGTH]
            logger.warning("Keyfile too short, regenerating")
        except OSError as e:
            logger.error("Error reading keyfile: %s", e)

    # Generate a new key
    key = secrets.token_bytes(_KEY_LENGTH)
    try:
        # Write with restrictive permissions (owner-only on Unix)
        fd = os.open(keyfile, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(key)
        logger.info("New encryption keyfile created at %s", keyfile)
    except OSError as e:
        logger.error("Error writing keyfile: %s", e)

    return key


def _get_fernet(base_path: str) -> "Fernet | None":
    """Create a Fernet instance from the stored key.

    Args:
        base_path: The application base directory.

    Returns:
        A Fernet instance, or None if cryptography is unavailable.
    """
    if not _HAS_FERNET:
        return None
    raw_key = _load_or_create_key(base_path)
    # Fernet requires a 32-byte url-safe base64-encoded key
    fernet_key = base64.urlsafe_b64encode(raw_key)
    return Fernet(fernet_key)


def encrypt_api_key(api_key: str, base_path: str) -> str:
    """Encrypt an API key for storage in settings.json.

    Uses Fernet encryption if available, otherwise base64 obfuscation.
    The returned string is prefixed with a marker so the decryption
    function can identify the method used.

    Args:
        api_key: The plaintext API key.
        base_path: The application base directory (for keyfile access).

    Returns:
        The encrypted/obfuscated string with a method prefix.
    """
    if not api_key:
        return ""

    fernet = _get_fernet(base_path)
    if fernet is not None:
        try:
            encrypted = fernet.encrypt(api_key.encode("utf-8"))
            return _FERNET_PREFIX + encrypted.decode("ascii")
        except Exception as e:
            logger.error("Fernet encryption failed, falling back to base64: %s", e)

    # Fallback: base64 obfuscation
    encoded = base64.b64encode(api_key.encode("utf-8")).decode("ascii")
    return _B64_PREFIX + encoded


def decrypt_api_key(stored_value: str, base_path: str) -> str:
    """Decrypt an API key from settings.json.

    Detects the encryption method from the prefix and decrypts
    accordingly. Plaintext values (no prefix) are returned as-is
    for backward compatibility with existing settings files.

    Args:
        stored_value: The encrypted/obfuscated string from settings.
        base_path: The application base directory (for keyfile access).

    Returns:
        The plaintext API key.
    """
    if not stored_value:
        return ""

    # Fernet-encrypted value
    if stored_value.startswith(_FERNET_PREFIX):
        token = stored_value[len(_FERNET_PREFIX):]
        fernet = _get_fernet(base_path)
        if fernet is not None:
            try:
                return fernet.decrypt(token.encode("ascii")).decode("utf-8")
            except Exception as e:
                logger.error("Fernet decryption failed: %s", e)
                return ""
        logger.error(
            "API key was encrypted with Fernet but cryptography library "
            "is not installed. Install it with: pip install cryptography"
        )
        return ""

    # Base64-obfuscated value
    if stored_value.startswith(_B64_PREFIX):
        encoded = stored_value[len(_B64_PREFIX):]
        try:
            return base64.b64decode(encoded.encode("ascii")).decode("utf-8")
        except Exception as e:
            logger.error("Base64 decoding failed: %s", e)
            return ""

    # Plaintext (legacy/unencrypted) — return as-is for backward compat
    logger.info("API key found in plaintext; it will be encrypted on next save")
    return stored_value


def mask_api_key(api_key: str) -> str:
    """Mask an API key for safe display in logs and status messages.

    Shows only the first 4 characters followed by asterisks.

    Args:
        api_key: The plaintext API key.

    Returns:
        The masked key string (e.g. 'abcd****').
    """
    if len(api_key) <= 4:
        return "****"
    return api_key[:4] + "****"
