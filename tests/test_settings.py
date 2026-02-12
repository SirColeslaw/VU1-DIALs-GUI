"""Tests for the SettingsManager (config loading/saving)."""

import json
import os

import pytest

from vu1_dials_gui.config.settings import SettingsManager


# ── load_settings ─────────────────────────────────────────────────────


class TestLoadSettings:
    def test_loads_valid_settings(self, tmp_base_path, sample_settings):
        """Settings with all required fields should load successfully."""
        path = os.path.join(tmp_base_path, "settings.json")
        with open(path, "w") as f:
            json.dump(sample_settings, f)

        mgr = SettingsManager(tmp_base_path)
        result = mgr.load_settings()
        assert result["server_address"] == sample_settings["server_address"]
        # API key is decrypted (plaintext passes through for backward compat)
        assert result["api_key"] == sample_settings["api_key"]
        assert result["minimize_to_tray"] == sample_settings["minimize_to_tray"]

    def test_returns_empty_when_no_file(self, tmp_base_path):
        """Missing settings file should return empty dict."""
        mgr = SettingsManager(tmp_base_path)
        result = mgr.load_settings()
        assert result == {}

    def test_returns_empty_when_missing_api_key(self, tmp_base_path):
        """Settings missing api_key should return empty dict."""
        path = os.path.join(tmp_base_path, "settings.json")
        with open(path, "w") as f:
            json.dump({"server_address": "http://localhost:5340"}, f)

        mgr = SettingsManager(tmp_base_path)
        result = mgr.load_settings()
        assert result == {}

    def test_returns_empty_when_missing_server(self, tmp_base_path):
        """Settings missing server_address should return empty dict."""
        path = os.path.join(tmp_base_path, "settings.json")
        with open(path, "w") as f:
            json.dump({"api_key": "some-key"}, f)

        mgr = SettingsManager(tmp_base_path)
        result = mgr.load_settings()
        assert result == {}

    def test_handles_corrupt_json(self, tmp_base_path):
        """Corrupt JSON should return empty dict without crashing."""
        path = os.path.join(tmp_base_path, "settings.json")
        with open(path, "w") as f:
            f.write("{invalid json")

        mgr = SettingsManager(tmp_base_path)
        result = mgr.load_settings()
        assert result == {}


# ── save_settings ─────────────────────────────────────────────────────


class TestSaveSettings:
    def test_saves_settings(self, tmp_base_path):
        """Settings should be written to the JSON file."""
        mgr = SettingsManager(tmp_base_path)
        success = mgr.save_settings(
            server_address="http://localhost:5340",
            api_key="my-secret-key",
            minimize_to_tray=True,
            start_in_tray=False,
            autostart=True,
        )
        assert success is True

        path = os.path.join(tmp_base_path, "settings.json")
        assert os.path.exists(path)

        with open(path) as f:
            saved = json.load(f)
        assert saved["server_address"] == "http://localhost:5340"
        assert saved["minimize_to_tray"] is True
        assert saved["autostart"] is True
        # API key should be encrypted (not plaintext)
        assert saved["api_key"] != "my-secret-key"
        assert saved["api_key"].startswith("enc:")

    def test_roundtrip(self, tmp_base_path):
        """save → load roundtrip should preserve all values."""
        mgr = SettingsManager(tmp_base_path)
        mgr.save_settings(
            server_address="https://myserver.local:9999",
            api_key="roundtrip-key-abc",
            minimize_to_tray=True,
            start_in_tray=True,
            autostart=False,
        )
        loaded = mgr.load_settings()
        assert loaded["server_address"] == "https://myserver.local:9999"
        assert loaded["api_key"] == "roundtrip-key-abc"
        assert loaded["minimize_to_tray"] is True
        assert loaded["start_in_tray"] is True
        assert loaded["autostart"] is False


# ── load_assignments ──────────────────────────────────────────────────


class TestLoadAssignments:
    def test_loads_valid_assignments(self, tmp_base_path, sample_assignments):
        path = os.path.join(tmp_base_path, "assignments.json")
        with open(path, "w") as f:
            json.dump(sample_assignments, f)

        mgr = SettingsManager(tmp_base_path)
        result = mgr.load_assignments()
        assert result["sensor_assignments"] == sample_assignments["sensor_assignments"]
        assert result["min_values"] == sample_assignments["min_values"]
        assert result["max_values"] == sample_assignments["max_values"]
        assert result["backlight_values"] == sample_assignments["backlight_values"]

    def test_returns_defaults_when_no_file(self, tmp_base_path):
        mgr = SettingsManager(tmp_base_path)
        result = mgr.load_assignments()
        assert result == {
            "sensor_assignments": {},
            "min_values": {},
            "max_values": {},
            "backlight_values": {},
        }

    def test_handles_partial_data(self, tmp_base_path):
        """Missing keys should be filled with empty dicts."""
        path = os.path.join(tmp_base_path, "assignments.json")
        with open(path, "w") as f:
            json.dump({"sensor_assignments": {"d1": "sensor1"}}, f)

        mgr = SettingsManager(tmp_base_path)
        result = mgr.load_assignments()
        assert result["sensor_assignments"] == {"d1": "sensor1"}
        assert result["min_values"] == {}
        assert result["max_values"] == {}
        assert result["backlight_values"] == {}


# ── save_assignments ──────────────────────────────────────────────────


class TestSaveAssignments:
    def test_saves_and_reloads(self, tmp_base_path, sample_assignments):
        mgr = SettingsManager(tmp_base_path)
        success = mgr.save_assignments(
            sensor_assignments=sample_assignments["sensor_assignments"],
            min_values=sample_assignments["min_values"],
            max_values=sample_assignments["max_values"],
            backlight_values=sample_assignments["backlight_values"],
        )
        assert success is True

        loaded = mgr.load_assignments()
        assert loaded["sensor_assignments"] == sample_assignments["sensor_assignments"]
        assert loaded["backlight_values"] == sample_assignments["backlight_values"]

    def test_saves_empty_assignments(self, tmp_base_path):
        mgr = SettingsManager(tmp_base_path)
        success = mgr.save_assignments(
            sensor_assignments={},
            min_values={},
            max_values={},
            backlight_values={},
        )
        assert success is True

        loaded = mgr.load_assignments()
        assert loaded["sensor_assignments"] == {}
