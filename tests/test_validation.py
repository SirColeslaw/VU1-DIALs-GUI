"""Tests for the validation module."""

import pytest

from vu1_dials_gui.validation import (
    sanitize_dial_name,
    sanitize_text_input,
    validate_api_key,
    validate_dial_name,
    validate_rgb_value,
    validate_server_address,
    validate_value_range,
)


# ── sanitize_dial_name ────────────────────────────────────────────────


class TestSanitizeDialName:
    def test_normal_name(self):
        assert sanitize_dial_name("CPU Temp") == "CPU Temp"

    def test_strips_whitespace(self):
        assert sanitize_dial_name("  hello  ") == "hello"

    def test_removes_control_characters(self):
        assert sanitize_dial_name("hello\x00world") == "helloworld"
        assert sanitize_dial_name("test\x1b[31m") == "test31m"

    def test_removes_special_characters(self):
        # Only word chars, spaces, hyphens, underscores, dots allowed
        assert sanitize_dial_name("name<script>") == "namescript"
        assert sanitize_dial_name("name&value") == "namevalue"

    def test_allows_hyphens_underscores_dots(self):
        assert sanitize_dial_name("cpu-temp_1.0") == "cpu-temp_1.0"

    def test_allows_unicode(self):
        assert sanitize_dial_name("Temperatur") == "Temperatur"

    def test_truncates_long_names(self):
        long_name = "A" * 100
        result = sanitize_dial_name(long_name)
        assert len(result) == 64

    def test_empty_string(self):
        assert sanitize_dial_name("") == ""

    def test_only_special_chars(self):
        assert sanitize_dial_name("<!@#$%^&*()>") == ""


# ── validate_dial_name ────────────────────────────────────────────────


class TestValidateDialName:
    def test_valid_name(self):
        valid, msg = validate_dial_name("CPU Temp")
        assert valid is True
        assert msg == ""

    def test_empty_name_invalid(self):
        valid, msg = validate_dial_name("")
        assert valid is False
        assert "empty" in msg.lower()

    def test_too_long_name(self):
        valid, msg = validate_dial_name("A" * 65)
        assert valid is False
        assert "64" in msg


# ── validate_server_address ───────────────────────────────────────────


class TestValidateServerAddress:
    def test_valid_http(self):
        valid, msg = validate_server_address("http://localhost:5340")
        assert valid is True
        assert msg == ""

    def test_valid_https(self):
        valid, msg = validate_server_address("https://example.com:5340")
        assert valid is True

    def test_empty_address(self):
        valid, msg = validate_server_address("")
        assert valid is False
        assert "empty" in msg.lower()

    def test_whitespace_only(self):
        valid, msg = validate_server_address("   ")
        assert valid is False

    def test_invalid_scheme_ftp(self):
        valid, msg = validate_server_address("ftp://example.com")
        assert valid is False
        assert "http" in msg.lower()

    def test_no_scheme(self):
        valid, msg = validate_server_address("localhost:5340")
        assert valid is False

    def test_injection_newline(self):
        valid, msg = validate_server_address("http://localhost\r\nHeader: injected")
        assert valid is False
        assert "invalid characters" in msg.lower()

    def test_injection_null_byte(self):
        valid, msg = validate_server_address("http://localhost\x00evil")
        assert valid is False

    def test_injection_semicolon(self):
        valid, msg = validate_server_address("http://localhost;rm -rf /")
        assert valid is False

    def test_strips_whitespace(self):
        valid, msg = validate_server_address("  http://localhost:5340  ")
        assert valid is True


# ── validate_api_key ──────────────────────────────────────────────────


class TestValidateApiKey:
    def test_valid_key(self):
        valid, msg = validate_api_key("abc123-XYZ")
        assert valid is True
        assert msg == ""

    def test_empty_key(self):
        valid, msg = validate_api_key("")
        assert valid is False
        assert "no api key" in msg.lower()

    def test_whitespace_only_key(self):
        valid, msg = validate_api_key("   ")
        assert valid is False

    def test_unprintable_chars(self):
        valid, msg = validate_api_key("key\x00value")
        assert valid is False
        assert "invalid characters" in msg.lower()

    def test_too_long_key(self):
        valid, msg = validate_api_key("A" * 513)
        assert valid is False
        assert "too long" in msg.lower()

    def test_max_length_key(self):
        valid, msg = validate_api_key("A" * 512)
        assert valid is True


# ── validate_value_range ──────────────────────────────────────────────


class TestValidateValueRange:
    def test_valid_range(self):
        valid, msg = validate_value_range(0, 100)
        assert valid is True
        assert msg == ""

    def test_negative_range(self):
        valid, msg = validate_value_range(-50, 50)
        assert valid is True

    def test_min_equals_max(self):
        valid, msg = validate_value_range(50, 50)
        assert valid is False
        assert "less than" in msg.lower()

    def test_min_greater_than_max(self):
        valid, msg = validate_value_range(100, 0)
        assert valid is False


# ── validate_rgb_value ────────────────────────────────────────────────


class TestValidateRgbValue:
    def test_normal_value(self):
        assert validate_rgb_value(128) == 128

    def test_min_boundary(self):
        assert validate_rgb_value(0) == 0

    def test_max_boundary(self):
        assert validate_rgb_value(255) == 255

    def test_below_min(self):
        assert validate_rgb_value(-10) == 0

    def test_above_max(self):
        assert validate_rgb_value(300) == 255


# ── sanitize_text_input ──────────────────────────────────────────────


class TestSanitizeTextInput:
    def test_normal_text(self):
        assert sanitize_text_input("Hello World") == "Hello World"

    def test_strips_whitespace(self):
        assert sanitize_text_input("  hello  ") == "hello"

    def test_removes_control_chars(self):
        assert sanitize_text_input("test\x00\x01\x1f") == "test"

    def test_truncates(self):
        result = sanitize_text_input("ABCDE", max_length=3)
        assert result == "ABC"

    def test_default_max_length(self):
        long_text = "A" * 300
        result = sanitize_text_input(long_text)
        assert len(result) == 255
