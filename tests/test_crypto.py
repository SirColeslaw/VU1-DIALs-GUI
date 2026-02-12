"""Tests for the crypto module (API key encryption at rest)."""

import base64
import os

import pytest

from vu1_dials_gui.config.crypto import (
    _B64_PREFIX,
    _KEYFILE_NAME,
    _load_or_create_key,
    decrypt_api_key,
    encrypt_api_key,
    mask_api_key,
)


# ── mask_api_key ──────────────────────────────────────────────────────


class TestMaskApiKey:
    def test_long_key(self):
        assert mask_api_key("abcdefghij") == "abcd****"

    def test_exactly_four_chars(self):
        assert mask_api_key("abcd") == "****"

    def test_short_key(self):
        assert mask_api_key("ab") == "****"

    def test_empty_key(self):
        assert mask_api_key("") == "****"

    def test_five_chars(self):
        assert mask_api_key("abcde") == "abcd****"


# ── _load_or_create_key ──────────────────────────────────────────────


class TestLoadOrCreateKey:
    def test_creates_keyfile(self, tmp_base_path):
        key = _load_or_create_key(tmp_base_path)
        assert len(key) == 32
        assert os.path.exists(os.path.join(tmp_base_path, _KEYFILE_NAME))

    def test_reloads_existing_key(self, tmp_base_path):
        key1 = _load_or_create_key(tmp_base_path)
        key2 = _load_or_create_key(tmp_base_path)
        assert key1 == key2

    def test_regenerates_short_keyfile(self, tmp_base_path):
        keyfile = os.path.join(tmp_base_path, _KEYFILE_NAME)
        with open(keyfile, "wb") as f:
            f.write(b"short")
        key = _load_or_create_key(tmp_base_path)
        assert len(key) == 32


# ── encrypt / decrypt roundtrip (base64 fallback) ────────────────────


class TestBase64Encryption:
    """Test the base64 fallback path (no cryptography library needed)."""

    def test_encrypt_produces_prefix(self, tmp_base_path, monkeypatch):
        # Force base64 fallback by pretending Fernet is unavailable
        import vu1_dials_gui.config.crypto as crypto_mod
        monkeypatch.setattr(crypto_mod, "_HAS_FERNET", False)

        result = encrypt_api_key("my-secret-key", tmp_base_path)
        assert result.startswith(_B64_PREFIX)

    def test_roundtrip(self, tmp_base_path, monkeypatch):
        import vu1_dials_gui.config.crypto as crypto_mod
        monkeypatch.setattr(crypto_mod, "_HAS_FERNET", False)

        original = "test-api-key-XYZ-123"
        encrypted = encrypt_api_key(original, tmp_base_path)
        decrypted = decrypt_api_key(encrypted, tmp_base_path)
        assert decrypted == original

    def test_empty_key_roundtrip(self, tmp_base_path, monkeypatch):
        import vu1_dials_gui.config.crypto as crypto_mod
        monkeypatch.setattr(crypto_mod, "_HAS_FERNET", False)

        assert encrypt_api_key("", tmp_base_path) == ""
        assert decrypt_api_key("", tmp_base_path) == ""

    def test_unicode_key_roundtrip(self, tmp_base_path, monkeypatch):
        import vu1_dials_gui.config.crypto as crypto_mod
        monkeypatch.setattr(crypto_mod, "_HAS_FERNET", False)

        original = "schluessel-mit-umlauten"
        encrypted = encrypt_api_key(original, tmp_base_path)
        decrypted = decrypt_api_key(encrypted, tmp_base_path)
        assert decrypted == original


# ── Backward compatibility with plaintext ─────────────────────────────


class TestPlaintextBackwardCompat:
    def test_plaintext_returned_as_is(self, tmp_base_path):
        """Existing plaintext API keys should still be readable."""
        result = decrypt_api_key("old-plaintext-key", tmp_base_path)
        assert result == "old-plaintext-key"


# ── Fernet encryption (if available) ─────────────────────────────────


class TestFernetEncryption:
    @pytest.fixture(autouse=True)
    def _check_fernet(self):
        """Skip if cryptography is not installed."""
        try:
            import cryptography  # noqa: F401
        except ImportError:
            pytest.skip("cryptography not installed")

    def test_fernet_roundtrip(self, tmp_base_path):
        original = "fernet-secret-key-456"
        encrypted = encrypt_api_key(original, tmp_base_path)
        assert encrypted.startswith("enc:fernet:")
        decrypted = decrypt_api_key(encrypted, tmp_base_path)
        assert decrypted == original

    def test_fernet_different_encryptions(self, tmp_base_path):
        """Fernet produces different ciphertexts for the same plaintext."""
        enc1 = encrypt_api_key("same-key", tmp_base_path)
        enc2 = encrypt_api_key("same-key", tmp_base_path)
        # Both should decrypt to the same value, but ciphertexts differ
        assert enc1 != enc2
        assert decrypt_api_key(enc1, tmp_base_path) == "same-key"
        assert decrypt_api_key(enc2, tmp_base_path) == "same-key"

    def test_wrong_keyfile_fails(self, tmp_base_path, tmp_path):
        """Decryption with a different key should fail gracefully."""
        encrypted = encrypt_api_key("secret", tmp_base_path)
        # Use a different temp dir (different keyfile)
        other_path = str(tmp_path / "other")
        os.makedirs(other_path)
        result = decrypt_api_key(encrypted, other_path)
        assert result == ""  # Decryption fails gracefully
