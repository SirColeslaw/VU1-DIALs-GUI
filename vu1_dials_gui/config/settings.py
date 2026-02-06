"""
Settings and assignments management.

Handles loading, saving, and validating application settings
and per-dial sensor assignments from JSON files. The API key
is encrypted at rest using the crypto module.
"""

import json
import logging
import os
import sys
from typing import Any

from ..constants import (
    ASSIGNMENTS_FILENAME,
    DEFAULT_API_KEY,
    DEFAULT_SERVER_ADDRESS,
    SETTINGS_FILENAME,
)
from .crypto import decrypt_api_key, encrypt_api_key

logger = logging.getLogger(__name__)


class SettingsManager:
    """Manages application settings and dial assignments persistence.

    Settings include server connection details, UI preferences, and
    autostart configuration. Assignments include sensor mappings,
    value ranges, and backlight colors per dial.
    """

    def __init__(self, base_path: str | None = None) -> None:
        """Initialize the settings manager.

        Args:
            base_path: Directory for settings files. Auto-detected if None.
        """
        if base_path is None:
            base_path = self._detect_base_path()
        self.base_path: str = base_path
        self.settings_file: str = os.path.join(self.base_path, SETTINGS_FILENAME)
        self.assignments_file: str = os.path.join(self.base_path, ASSIGNMENTS_FILENAME)

    @staticmethod
    def _detect_base_path() -> str:
        """Detect the application base path for script or frozen exe mode.

        Returns:
            The directory containing the application.
        """
        if getattr(sys, "frozen", False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(sys.argv[0]))

    def load_settings(self) -> dict[str, Any]:
        """Load application settings from the JSON file.

        The API key is decrypted transparently. Plaintext keys from
        older settings files are accepted and will be encrypted on
        the next save.

        Returns:
            A dictionary of settings, or empty dict if loading fails
            or required fields are missing.
        """
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r") as file:
                    settings = json.load(file)
                    if not settings.get("server_address") or not settings.get("api_key"):
                        logger.warning("Settings file missing required fields (server_address/api_key)")
                        return {}
                    # Decrypt the API key
                    settings["api_key"] = decrypt_api_key(
                        settings["api_key"], self.base_path,
                    )
                    return settings
            logger.info("No settings file found at %s, using defaults", self.settings_file)
            return {}
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Error loading settings: %s", e)
            return {}

    def save_settings(
        self,
        server_address: str,
        api_key: str,
        minimize_to_tray: bool,
        start_in_tray: bool,
        autostart: bool,
    ) -> bool:
        """Save application settings to the JSON file.

        The API key is encrypted before writing so it is never
        stored in plaintext.

        Args:
            server_address: The VU1 server URL.
            api_key: The API authentication key (plaintext).
            minimize_to_tray: Whether to minimize to system tray.
            start_in_tray: Whether to start minimized in tray.
            autostart: Whether to start with Windows.

        Returns:
            True if settings were saved successfully, False otherwise.
        """
        try:
            settings = {
                "server_address": server_address,
                "api_key": encrypt_api_key(api_key, self.base_path),
                "minimize_to_tray": minimize_to_tray,
                "start_in_tray": start_in_tray,
                "autostart": autostart,
            }
            with open(self.settings_file, "w") as f:
                json.dump(settings, f, indent=4)
            logger.info("Settings saved successfully")
            return True
        except OSError as e:
            logger.error("Error saving settings: %s", e)
            return False

    def load_assignments(self) -> dict[str, Any]:
        """Load dial assignments from the JSON file.

        Returns:
            A dictionary containing sensor_assignments, min_values,
            max_values, and backlight_values. Empty sub-dicts on failure.
        """
        default = {
            "sensor_assignments": {},
            "min_values": {},
            "max_values": {},
            "backlight_values": {},
        }
        try:
            if os.path.exists(self.assignments_file):
                with open(self.assignments_file, "r") as file:
                    data = json.load(file)
                    return {
                        "sensor_assignments": data.get("sensor_assignments", {}),
                        "min_values": data.get("min_values", {}),
                        "max_values": data.get("max_values", {}),
                        "backlight_values": data.get("backlight_values", {}),
                    }
            logger.info("No assignments file found at %s", self.assignments_file)
            return default
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Error loading assignments: %s", e)
            return default

    def save_assignments(
        self,
        sensor_assignments: dict[str, str],
        min_values: dict[str, int],
        max_values: dict[str, int],
        backlight_values: dict[str, dict[str, int]],
    ) -> bool:
        """Save dial assignments to the JSON file.

        Args:
            sensor_assignments: Mapping of dial_id to sensor text.
            min_values: Mapping of dial_id to minimum value.
            max_values: Mapping of dial_id to maximum value.
            backlight_values: Mapping of dial_id to RGB dict.

        Returns:
            True if assignments were saved successfully, False otherwise.
        """
        try:
            data = {
                "sensor_assignments": sensor_assignments,
                "min_values": min_values,
                "max_values": max_values,
                "backlight_values": backlight_values,
            }
            with open(self.assignments_file, "w") as file:
                json.dump(data, file, indent=4)
            logger.info("Assignments saved successfully")
            return True
        except OSError as e:
            logger.error("Error saving assignments: %s", e)
            return False
