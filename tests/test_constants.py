"""Tests for constants module — verify critical values haven't drifted."""

from vu1_dials_gui.constants import (
    API_BASE_PATH,
    DEFAULT_EASING_PERIOD,
    DEFAULT_EASING_STEP,
    DEFAULT_MAX_VALUE,
    DEFAULT_MIN_VALUE,
    DEFAULT_SERVER_ADDRESS,
    DIAL_NAME_MAX_LENGTH,
    DIAL_NAME_PATTERN,
    EASING_PERIOD_MAX,
    EASING_STEP_MAX,
    RGB_API_MAX,
    RGB_MAX,
    SENSOR_UPDATE_INTERVAL_MS,
    SUPPORTED_IMAGE_EXTENSIONS,
)


class TestConstants:
    def test_server_defaults(self):
        assert DEFAULT_SERVER_ADDRESS == "http://localhost:5340"
        assert API_BASE_PATH == "/api/v0"

    def test_rgb_range(self):
        assert RGB_MAX == 255
        assert RGB_API_MAX == 100

    def test_value_defaults(self):
        assert DEFAULT_MIN_VALUE == 0
        assert DEFAULT_MAX_VALUE == 100

    def test_easing_defaults(self):
        assert DEFAULT_EASING_PERIOD == 50
        assert DEFAULT_EASING_STEP == 5
        assert EASING_PERIOD_MAX == 1000
        assert EASING_STEP_MAX == 100

    def test_sensor_interval(self):
        assert SENSOR_UPDATE_INTERVAL_MS == 1000

    def test_image_extensions(self):
        assert ".png" in SUPPORTED_IMAGE_EXTENSIONS
        assert ".jpg" in SUPPORTED_IMAGE_EXTENSIONS
        assert ".jpeg" in SUPPORTED_IMAGE_EXTENSIONS

    def test_dial_name_max_length(self):
        assert DIAL_NAME_MAX_LENGTH == 64

    def test_dial_name_pattern_allows_safe_chars(self):
        assert DIAL_NAME_PATTERN.sub("", "Hello World-1_2.3") == "Hello World-1_2.3"

    def test_dial_name_pattern_removes_unsafe_chars(self):
        assert DIAL_NAME_PATTERN.sub("", "<script>alert(1)</script>") == "scriptalert1script"
