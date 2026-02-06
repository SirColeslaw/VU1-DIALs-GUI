"""
Input validation and sanitization.

Provides validation functions for all user-facing inputs
to prevent injection, malformed data, and out-of-range values.
"""

import logging
import re
from urllib.parse import urlparse

from .constants import (
    DIAL_NAME_MAX_LENGTH,
    DIAL_NAME_PATTERN,
    SERVER_ADDRESS_SCHEMES,
)

logger = logging.getLogger(__name__)


def sanitize_dial_name(name: str) -> str:
    """Sanitize a dial name by removing unsafe characters.

    Strips leading/trailing whitespace, removes control characters,
    and truncates to the maximum allowed length.

    Args:
        name: The raw user input for a dial name.

    Returns:
        The sanitized name string.
    """
    # Strip whitespace
    name = name.strip()

    # Remove control characters (keep printable chars, including unicode letters)
    name = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", name)

    # Remove characters that are not allowed by the pattern
    name = DIAL_NAME_PATTERN.sub("", name)

    # Truncate to max length
    if len(name) > DIAL_NAME_MAX_LENGTH:
        name = name[:DIAL_NAME_MAX_LENGTH]
        logger.warning("Dial name truncated to %d characters", DIAL_NAME_MAX_LENGTH)

    return name


def validate_dial_name(name: str) -> tuple[bool, str]:
    """Validate a dial name and return a user-friendly error message.

    Args:
        name: The sanitized dial name.

    Returns:
        A tuple of (is_valid, error_message). error_message is empty if valid.
    """
    if not name:
        return False, "Dial name cannot be empty."

    if len(name) > DIAL_NAME_MAX_LENGTH:
        return False, f"Dial name must be {DIAL_NAME_MAX_LENGTH} characters or less."

    return True, ""


def validate_server_address(address: str) -> tuple[bool, str]:
    """Validate a server address URL.

    Checks for proper URL format, allowed schemes (http/https),
    and the presence of a hostname.

    Args:
        address: The server address to validate.

    Returns:
        A tuple of (is_valid, error_message). error_message is empty if valid.
    """
    address = address.strip()

    if not address:
        return False, "Server address cannot be empty."

    try:
        parsed = urlparse(address)
    except ValueError:
        return False, "Invalid URL format."

    if parsed.scheme not in SERVER_ADDRESS_SCHEMES:
        return False, f"Server address must use {' or '.join(SERVER_ADDRESS_SCHEMES)}."

    if not parsed.hostname:
        return False, "Server address must include a hostname."

    # Check for suspicious characters that could indicate injection
    if any(c in address for c in ["\n", "\r", "\x00", ";"]):
        return False, "Server address contains invalid characters."

    return True, ""


def validate_api_key(api_key: str) -> tuple[bool, str]:
    """Validate an API key.

    Checks that the key is non-empty and contains only safe characters.

    Args:
        api_key: The API key to validate.

    Returns:
        A tuple of (is_valid, error_message). error_message is empty if valid.
    """
    api_key = api_key.strip()

    if not api_key:
        return False, "No API key was provided!\nPlease enter a valid API key."

    # API keys should only contain printable ASCII (no control chars)
    if not api_key.isprintable():
        return False, "API key contains invalid characters."

    # Check for suspiciously long keys
    if len(api_key) > 512:
        return False, "API key is too long."

    return True, ""


def sanitize_text_input(text: str, max_length: int = 255) -> str:
    """General-purpose text sanitization.

    Strips whitespace and control characters, truncates to max length.

    Args:
        text: The raw user input.
        max_length: Maximum allowed length.

    Returns:
        The sanitized text.
    """
    text = text.strip()
    text = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", text)
    return text[:max_length]


def validate_rgb_value(value: int) -> int:
    """Clamp an RGB value to the valid 0-255 range.

    Args:
        value: The RGB value to validate.

    Returns:
        The clamped value.
    """
    return max(0, min(255, int(value)))


def validate_value_range(min_value: int, max_value: int) -> tuple[bool, str]:
    """Validate that a min/max value range is sensible.

    Args:
        min_value: The minimum value.
        max_value: The maximum value.

    Returns:
        A tuple of (is_valid, error_message). error_message is empty if valid.
    """
    if min_value >= max_value:
        return False, "Minimum value must be less than maximum value."
    return True, ""
