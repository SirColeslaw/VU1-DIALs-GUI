"""Shared fixtures for the VU1 DIALs GUI test suite."""

import os
import json
import pytest


@pytest.fixture
def tmp_base_path(tmp_path):
    """Provide a temporary directory that acts as the app base path."""
    return str(tmp_path)


@pytest.fixture
def sample_settings():
    """Return a sample settings dictionary."""
    return {
        "server_address": "http://localhost:5340",
        "api_key": "test-api-key-12345",
        "minimize_to_tray": False,
        "start_in_tray": False,
        "autostart": False,
    }


@pytest.fixture
def sample_assignments():
    """Return a sample assignments dictionary."""
    return {
        "sensor_assignments": {
            "dial-001": "CPU Temperature (TCPU)",
            "dial-002": "GPU Temperature (TGPU)",
        },
        "min_values": {"dial-001": 20, "dial-002": 30},
        "max_values": {"dial-001": 100, "dial-002": 90},
        "backlight_values": {
            "dial-001": {"red": 255, "green": 0, "blue": 0},
            "dial-002": {"red": 0, "green": 255, "blue": 0},
        },
    }


@pytest.fixture
def settings_file(tmp_base_path, sample_settings):
    """Create a settings.json file in the temp directory and return its path."""
    path = os.path.join(tmp_base_path, "settings.json")
    with open(path, "w") as f:
        json.dump(sample_settings, f)
    return path


@pytest.fixture
def assignments_file(tmp_base_path, sample_assignments):
    """Create an assignments.json file in the temp directory and return its path."""
    path = os.path.join(tmp_base_path, "assignments.json")
    with open(path, "w") as f:
        json.dump(sample_assignments, f)
    return path
