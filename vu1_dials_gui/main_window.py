"""
Main application window for the VU1 DIALs GUI.

Orchestrates all components: dial widgets, API communication,
sensor data polling, and user settings management.
"""

import logging
import os
import sys
from typing import Any

from PyQt6.QtCore import QEvent, QTimer, Qt
from PyQt6.QtGui import QColor, QIcon, QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QColorDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStyle,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from .api.client import VU1ApiClient
from .config.settings import SettingsManager
from .validation import (
    sanitize_dial_name,
    validate_api_key,
    validate_dial_name,
    validate_server_address,
    validate_value_range,
)
from .constants import (
    AUTOSTART_APP_NAME,
    AUTOSTART_REGISTRY_PATH,
    DEFAULT_API_KEY,
    DEFAULT_EASING_PERIOD,
    DEFAULT_EASING_STEP,
    DEFAULT_MAX_VALUE,
    DEFAULT_MIN_VALUE,
    DEFAULT_SERVER_ADDRESS,
    HEADER_MAX_HEIGHT,
    HEADER_STYLE,
    HEADER_TITLE,
    ICON_FILENAME,
    IMAGE_FILE_FILTER,
    MAIN_LAYOUT_MARGIN,
    MAIN_LAYOUT_SPACING,
    SENSOR_UPDATE_INTERVAL_MS,
    SUPPORTED_IMAGE_EXTENSIONS,
    TRAY_TOOLTIP,
    WINDOW_DEFAULT_HEIGHT,
    WINDOW_DEFAULT_WIDTH,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
    WINDOW_RESIZE_MIN_HEIGHT,
    WINDOW_RESIZE_MIN_WIDTH,
    WINDOW_TITLE,
)
from .widgets.dial_widget import DialWidget
from .widgets.flow_layout import FlowLayout
from .widgets.settings_dialog import SettingsDialog

logger = logging.getLogger(__name__)


class VU1GUI(QMainWindow):
    """Main application window that manages VU1 dials.

    Coordinates between the UI widgets, the VU1 Server API,
    AIDA64 sensor data, and persistent configuration. Acts as
    the central controller for the application lifecycle.
    """

    def __init__(self) -> None:
        """Initialize the main window, load settings, and set up all components."""
        super().__init__()

        QApplication.instance().aboutToQuit.connect(self.shutdown_dials)

        # Configuration
        self.settings_manager = SettingsManager()
        settings = self.settings_manager.load_settings()

        self.autostart_enabled: bool = settings.get("autostart", False)
        self.minimize_to_tray: bool = settings.get("minimize_to_tray", False)
        self.start_in_tray: bool = settings.get("start_in_tray", False)
        self.server_address: str = settings.get("server_address", DEFAULT_SERVER_ADDRESS)
        self.api_key: str = settings.get("api_key", DEFAULT_API_KEY)
        self.backlight_values: dict[str, dict[str, int]] = {}

        # API client
        self.api_client = VU1ApiClient(self.server_address, self.api_key)

        # Basic window setup
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        self.center_window()

        # If no server address or API key is set, show settings dialog
        if not self.server_address or not self.api_key:
            self._show_settings_dialog()

        # Widgets and data
        self.dial_widgets: dict[str, DialWidget] = {}
        self.sensor_assignments: dict[str, str] = {}
        self.min_values: dict[str, int] = {}
        self.max_values: dict[str, int] = {}

        # GUI setup
        self._setup_ui()

        # Initial fetch of AIDA64 data
        self.statusBar().showMessage("Load AIDA64 Sensor data...")
        self.aida64_data: dict[str, Any] = self._fetch_aida64_data()

        # Load assignments from JSON file
        self._load_assignments()

        # Timer for sensor updates
        self.update_timer = QTimer()
        self.update_timer.setInterval(SENSOR_UPDATE_INTERVAL_MS)
        self.update_timer.timeout.connect(self._schedule_sensor_updates)

        # Fetch all dial details
        self._fetch_all_dial_details()
        self.update_timer.start()

        self.statusBar().showMessage("Ready")

        # Tray Icon Setup
        self._setup_tray_icon()

        # If start in tray is enabled, hide the window and show the tray icon
        if self.start_in_tray:
            self.hide()
            self.tray_icon.show()
        else:
            self.show()

    # ── UI Setup ──────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        """Build the main window UI layout with header and dials container."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)

        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(MAIN_LAYOUT_SPACING)
        main_layout.setContentsMargins(
            MAIN_LAYOUT_MARGIN, MAIN_LAYOUT_MARGIN,
            MAIN_LAYOUT_MARGIN, MAIN_LAYOUT_MARGIN,
        )

        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header.setMaximumHeight(HEADER_MAX_HEIGHT)

        title = QLabel(HEADER_TITLE)
        title.setStyleSheet(HEADER_STYLE)
        settings_btn = QPushButton("Settings")
        settings_btn.clicked.connect(self._show_settings_dialog)
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(settings_btn)
        main_layout.addWidget(header)

        # Dials container with flow layout
        self.dials_container = QWidget()
        self.dials_layout = FlowLayout(self.dials_container)
        self.dials_container.setLayout(self.dials_layout)
        main_layout.addWidget(self.dials_container)

        self.statusBar().showMessage("Ready")

    def _setup_tray_icon(self) -> None:
        """Initialize the system tray icon and its behavior."""
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = os.path.join(self.settings_manager.base_path, ICON_FILENAME)
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
        else:
            icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip(TRAY_TOOLTIP)
        self.tray_icon.activated.connect(self._tray_icon_activated)

    # ── Dial Widget Management ────────────────────────────────────────

    def _create_dial_widget(self, details: dict[str, Any], dial_id: str) -> None:
        """Create or replace a dial widget with fresh data.

        Args:
            details: Dictionary with 'status' and 'image' data from the API.
            dial_id: The unique identifier of the dial.
        """
        try:
            # Remove existing widget if it exists
            if dial_id in self.dial_widgets:
                old_widget = self.dial_widgets[dial_id]
                self.dials_layout.removeWidget(old_widget)
                old_widget.deleteLater()

            widget = DialWidget(dial_id=dial_id)
            self.dial_widgets[dial_id] = widget

            # Connect signals
            widget.set_image_btn.clicked.connect(
                lambda checked=False, did=dial_id: self._set_image_for_dial(did))
            widget.save_name_btn.clicked.connect(
                lambda checked=False, did=dial_id: self._set_dial_name(did, self.dial_widgets[did].name_input.text()))
            widget.color_picker_btn.clicked.connect(
                lambda checked=False, did=dial_id: self._show_color_picker(did))
            widget.save_backlight_btn.clicked.connect(
                lambda checked=False, did=dial_id: self._set_backlight(
                    did,
                    self.dial_widgets[did].red_spin.value(),
                    self.dial_widgets[did].green_spin.value(),
                    self.dial_widgets[did].blue_spin.value(),
                ))
            widget.assign_sensor_btn.clicked.connect(
                lambda checked=False, did=dial_id: self._assign_sensor_to_dial(
                    did, self.dial_widgets[did].sensor_combo.currentText()))
            widget.save_range_btn.clicked.connect(
                lambda checked=False, did=dial_id: self._set_value_range(
                    did,
                    self.dial_widgets[did].min_value.value(),
                    self.dial_widgets[did].max_value.value(),
                ))
            widget.save_easing_btn.clicked.connect(
                lambda checked=False, did=dial_id: self._set_dial_easing(
                    did,
                    self.dial_widgets[did].period_spin.value(),
                    self.dial_widgets[did].step_spin.value(),
                ))

            # Update widget with data
            self._update_dial_widget_with_data(widget, details)
            self.dials_layout.addWidget(widget)

            # Restore stored backlight levels
            if dial_id in self.backlight_values:
                saved = self.backlight_values[dial_id]
                widget.red_spin.setValue(saved["red"])
                widget.green_spin.setValue(saved["green"])
                widget.blue_spin.setValue(saved["blue"])
                self._set_backlight(dial_id, saved["red"], saved["green"], saved["blue"])

            self.adjustSize()

        except Exception as e:
            logger.error("Error creating widget for dial %s: %s", dial_id, e)

    def _update_dial_widget_with_data(self, widget: DialWidget, details: dict[str, Any]) -> None:
        """Refresh a dial widget's display with API data and local settings.

        Args:
            widget: The DialWidget to update.
            details: Dictionary with 'status' and 'image' data from the API.
        """
        try:
            status_data = (details.get("status") or {}).get("data", {})

            # Update name
            name = status_data.get("dial_name", "")
            widget.name_input.setText(name)

            # Update image
            if details.get("image"):
                image = QImage.fromData(details["image"])
                if not image.isNull():
                    scaled_pixmap = QPixmap.fromImage(image).scaled(
                        widget.image_label.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    widget.image_label.setPixmap(scaled_pixmap)

            # Set min/max values from local settings
            widget.min_value.setValue(
                int(float(self.min_values.get(widget.dial_id, DEFAULT_MIN_VALUE))))
            widget.max_value.setValue(
                int(float(self.max_values.get(widget.dial_id, DEFAULT_MAX_VALUE))))

            # Update sensor combo box
            if self.aida64_data:
                widget.sensor_combo.clear()
                sensor_options: list[str] = []
                for category in self.aida64_data.values():
                    if isinstance(category, list):
                        for item in category:
                            if "label" in item and "id" in item:
                                sensor_options.append(f"{item['label']} ({item['id']})")

                widget.sensor_combo.addItems(sorted(sensor_options))

                if widget.dial_id in self.sensor_assignments:
                    index = widget.sensor_combo.findText(
                        self.sensor_assignments[widget.dial_id])
                    if index >= 0:
                        widget.sensor_combo.setCurrentIndex(index)

            # Update easing parameters
            easing = status_data.get("easing", {})
            if easing:
                widget.period_spin.setValue(int(easing.get("dial_period", DEFAULT_EASING_PERIOD)))
                widget.step_spin.setValue(int(easing.get("dial_step", DEFAULT_EASING_STEP)))

        except Exception as e:
            logger.error("Error updating widget: %s", e)

    # ── Settings Dialog ───────────────────────────────────────────────

    def _show_settings_dialog(self) -> None:
        """Open the settings dialog, validate all inputs, and save."""
        dialog = SettingsDialog(self)
        dialog.server_input.setText(self.server_address)
        dialog.api_key_input.setText(self.api_key)
        dialog.minimize_to_tray.setChecked(self.minimize_to_tray)
        dialog.autostart.setChecked(self.autostart_enabled)
        dialog.start_in_tray.setChecked(self.start_in_tray)

        if dialog.exec():
            # Validate server address format
            server_addr = dialog.server_input.text().strip()
            valid, msg = validate_server_address(server_addr)
            if not valid:
                QMessageBox.critical(
                    self, "Error", msg, QMessageBox.StandardButton.Ok,
                )
                self._show_settings_dialog()
                return

            # Validate API key
            api_key = dialog.api_key_input.text().strip()
            valid, msg = validate_api_key(api_key)
            if not valid:
                QMessageBox.critical(
                    self, "Error", msg, QMessageBox.StandardButton.Ok,
                )
                self._show_settings_dialog()
                return

            # Validate server connectivity
            try:
                self.api_client.test_connection(server_addr, api_key)
            except Exception as e:
                self._handle_connection_error(e, server_addr)
                return

            # Save validated settings
            self.server_address = server_addr
            self.api_key = api_key
            self.minimize_to_tray = dialog.minimize_to_tray.isChecked()
            self.start_in_tray = dialog.start_in_tray.isChecked()

            # Update API client with new credentials
            self.api_client.server_address = self.server_address
            self.api_client.api_key = self.api_key

            if dialog.autostart.isChecked() != self.autostart_enabled:
                self._set_autostart(dialog.autostart.isChecked())

            self.settings_manager.save_settings(
                self.server_address,
                self.api_key,
                self.minimize_to_tray,
                self.start_in_tray,
                self.autostart_enabled,
            )

    def _handle_connection_error(self, error: Exception, server_address: str) -> None:
        """Show appropriate error message for connection failures.

        Args:
            error: The exception that occurred.
            server_address: The server address that failed.
        """
        import requests
        if isinstance(error, (requests.ConnectionError, requests.Timeout)):
            QMessageBox.critical(
                self, "Error",
                f"The server at {server_address} is unavailable!\n"
                "Please check the server address and your network connection.",
                QMessageBox.StandardButton.Ok,
            )
        else:
            QMessageBox.critical(
                self, "Error",
                f"Error connecting to the server: {error}",
                QMessageBox.StandardButton.Ok,
            )
        self._show_settings_dialog()

    # ── Sensor Data ───────────────────────────────────────────────────

    def _schedule_sensor_updates(self) -> None:
        """Periodically fetch fresh sensor data and update all dials."""
        self.aida64_data = self._fetch_aida64_data()
        self._update_all_dials()

    def _update_all_dials(self) -> None:
        """Update every assigned dial with the latest sensor data."""
        for dial_id in self.sensor_assignments:
            self._update_dial_with_sensor_data(dial_id)

    def _update_dial_with_sensor_data(self, dial_id: str) -> None:
        """Update a single dial by reading its assigned sensor value.

        Args:
            dial_id: The unique identifier of the dial to update.
        """
        try:
            sensor = self.sensor_assignments.get(dial_id)
            if not sensor:
                return

            sensor_id = sensor.split("(")[-1].strip(")")
            sensor_data = None
            for category in self.aida64_data.values():
                if isinstance(category, list):
                    found = next((item for item in category if item["id"] == sensor_id), None)
                    if found:
                        sensor_data = found
                        break

            if sensor_data and "value" in sensor_data:
                value = float(sensor_data["value"])
                min_val = self.min_values.get(dial_id, DEFAULT_MIN_VALUE)
                max_val = self.max_values.get(dial_id, DEFAULT_MAX_VALUE)
                mapped_value = self._map_value_to_range(value, min_val, max_val)
                self.api_client.set_dial_value(dial_id, mapped_value)
        except Exception as e:
            logger.error("Error updating dial %s: %s", dial_id, e)

    @staticmethod
    def _fetch_aida64_data() -> dict[str, Any]:
        """Fetch the latest sensor data from AIDA64 shared memory.

        Returns:
            A dictionary of sensor categories and their readings.
        """
        try:
            from python_aida64 import getData
            return getData()
        except Exception as e:
            logger.error("Error retrieving AIDA64 data: %s", e)
            return {}

    @staticmethod
    def _map_value_to_range(value: float, min_value: float, max_value: float) -> float:
        """Map a sensor value to the 0-100 dial range.

        Args:
            value: The raw sensor value.
            min_value: The configured minimum of the sensor range.
            max_value: The configured maximum of the sensor range.

        Returns:
            The mapped value clamped to 0-100.
        """
        try:
            return max(0.0, min(100.0, ((value - min_value) / (max_value - min_value)) * 100))
        except (ZeroDivisionError, TypeError):
            return 0.0

    # ── Dial API Actions ──────────────────────────────────────────────

    def _fetch_all_dial_details(self) -> None:
        """Fetch the list of dials from the server and create widgets for each."""
        try:
            dials = self.api_client.get_dial_list()

            # Remove existing widgets
            for widget in self.dial_widgets.values():
                widget.deleteLater()
            self.dial_widgets.clear()

            # Create new widgets for each dial
            for dial in dials:
                details = self.api_client.fetch_dial_details(dial["uid"])
                self._create_dial_widget(details, dial["uid"])

            self.adjustSize()
            self.center_window()

        except Exception as e:
            logger.error("Error retrieving dial list: %s", e)
            QMessageBox.warning(
                self, "Error",
                f"Error retrieving the dials: {e}",
            )

    def _set_image_for_dial(self, dial_id: str) -> None:
        """Open a file dialog and upload the selected image to a dial.

        Args:
            dial_id: The unique identifier of the dial.
        """
        try:
            file_path = QFileDialog.getOpenFileName(
                self, "Select an image", "", IMAGE_FILE_FILTER,
            )[0]

            if not file_path:
                return

            if not file_path.lower().endswith(SUPPORTED_IMAGE_EXTENSIONS):
                QMessageBox.warning(self, "Error", "Please select a PNG or JPG file.")
                return

            with open(file_path, "rb") as image_file:
                success = self.api_client.set_dial_image(dial_id, image_file)

            if success:
                details = self.api_client.fetch_dial_details(dial_id)
                self._update_dial_widget_with_data(self.dial_widgets[dial_id], details)
                self.statusBar().showMessage(
                    f"New image for dial {dial_id} set: {os.path.basename(file_path)}")
            else:
                QMessageBox.warning(self, "Error", "Error setting image.")

        except Exception as e:
            logger.error("Error setting image for dial %s: %s", dial_id, e)
            QMessageBox.warning(self, "Error", f"Error setting image: {e}")

    def _set_dial_name(self, dial_id: str, new_name: str) -> None:
        """Sanitize, validate, and set a new display name for a dial.

        Args:
            dial_id: The unique identifier of the dial.
            new_name: The raw name input from the user.
        """
        try:
            # Sanitize and validate the name
            sanitized = sanitize_dial_name(new_name)
            valid, msg = validate_dial_name(sanitized)
            if not valid:
                QMessageBox.warning(self, "Error", msg)
                return

            if self.api_client.set_dial_name(dial_id, sanitized):
                details = self.api_client.fetch_dial_details(dial_id)
                self._update_dial_widget_with_data(self.dial_widgets[dial_id], details)
                self.statusBar().showMessage(f"Name for dial {dial_id} set to '{sanitized}'")
            else:
                QMessageBox.warning(self, "Error", "Error setting name.")
        except Exception as e:
            logger.error("Error setting name for dial %s: %s", dial_id, e)
            QMessageBox.warning(self, "Error", f"Error setting name: {e}")

    def _show_color_picker(self, dial_id: str) -> None:
        """Open a color picker and apply the selected color to the dial's spin boxes.

        Args:
            dial_id: The unique identifier of the dial.
        """
        color = QColorDialog.getColor()
        if color.isValid():
            widget = self.dial_widgets[dial_id]
            widget.red_spin.setValue(color.red())
            widget.green_spin.setValue(color.green())
            widget.blue_spin.setValue(color.blue())

    def _set_backlight(self, dial_id: str, red: int, green: int, blue: int) -> None:
        """Set the backlight color for a dial via the API and store locally.

        Args:
            dial_id: The unique identifier of the dial.
            red: Red channel value (0-255).
            green: Green channel value (0-255).
            blue: Blue channel value (0-255).
        """
        try:
            if self.api_client.set_backlight(dial_id, red, green, blue):
                self.backlight_values[dial_id] = {"red": red, "green": green, "blue": blue}
                self.statusBar().showMessage(
                    f"Backlight for dial {dial_id} set to RGB({red}, {green}, {blue})")
            else:
                QMessageBox.warning(self, "Error", "Error setting backlight.")
        except Exception as e:
            logger.error("Error setting backlight for dial %s: %s", dial_id, e)
            QMessageBox.warning(self, "Error", f"Error setting backlight: {e}")

    def _assign_sensor_to_dial(self, dial_id: str, sensor_text: str) -> None:
        """Assign an AIDA64 sensor to a dial and persist the assignment.

        Args:
            dial_id: The unique identifier of the dial.
            sensor_text: The sensor label text from the combo box.
        """
        try:
            if not sensor_text:
                return

            self.sensor_assignments[dial_id] = sensor_text
            self._save_assignments()
            self._update_dial_with_sensor_data(dial_id)

            sensor_name = sensor_text.split(" (")[0]
            self.statusBar().showMessage(f"Sensor '{sensor_name}' assigned to dial {dial_id}")

        except Exception as e:
            logger.error("Error assigning sensor for dial %s: %s", dial_id, e)
            QMessageBox.warning(self, "Error", f"Error assigning sensor: {e}")

    def _set_value_range(self, dial_id: str, min_value: int, max_value: int) -> None:
        """Validate and save the value range for a dial, then update.

        Args:
            dial_id: The unique identifier of the dial.
            min_value: The minimum sensor value for mapping.
            max_value: The maximum sensor value for mapping.
        """
        try:
            valid, msg = validate_value_range(int(min_value), int(max_value))
            if not valid:
                QMessageBox.warning(self, "Error", msg)
                return

            self.min_values[dial_id] = int(min_value)
            self.max_values[dial_id] = int(max_value)
            self._save_assignments()
            self._update_dial_with_sensor_data(dial_id)
            self.statusBar().showMessage(
                f"Value range for dial {dial_id} set to {min_value} - {max_value}")
        except Exception as e:
            logger.error("Error setting value range for dial %s: %s", dial_id, e)
            QMessageBox.warning(self, "Error", f"Error setting value range: {e}")

    def _set_dial_easing(self, dial_id: str, period: int, step: int) -> None:
        """Set easing parameters for smooth dial movement via the API.

        Args:
            dial_id: The unique identifier of the dial.
            period: Update period in milliseconds.
            step: Maximum step size in percent per update.
        """
        try:
            if self.api_client.set_dial_easing(dial_id, period, step):
                self.statusBar().showMessage(f"Easing parameters for dial {dial_id} updated")
            else:
                QMessageBox.warning(self, "Error", "Error setting easing parameters.")
        except Exception as e:
            logger.error("Error setting easing for dial %s: %s", dial_id, e)
            QMessageBox.warning(self, "Error", f"Error setting easing parameters: {e}")

    # ── Persistence ───────────────────────────────────────────────────

    def _load_assignments(self) -> None:
        """Load dial assignments from the settings manager."""
        data = self.settings_manager.load_assignments()
        self.sensor_assignments = data["sensor_assignments"]
        self.min_values = data["min_values"]
        self.max_values = data["max_values"]
        self.backlight_values = data["backlight_values"]
        self.statusBar().showMessage("Settings and assignments loaded")

    def _save_assignments(self) -> None:
        """Collect current backlight values and save all assignments."""
        for dial_id, widget in self.dial_widgets.items():
            self.backlight_values[dial_id] = {
                "red": widget.red_spin.value(),
                "green": widget.green_spin.value(),
                "blue": widget.blue_spin.value(),
            }

        success = self.settings_manager.save_assignments(
            self.sensor_assignments,
            self.min_values,
            self.max_values,
            self.backlight_values,
        )
        if success:
            self.statusBar().showMessage("Settings and assignments saved")
        else:
            QMessageBox.warning(self, "Error", "The assignments could not be saved.")

    # ── Window Events ─────────────────────────────────────────────────

    def closeEvent(self, event: QEvent) -> None:
        """Handle window close: shutdown dials and save all settings.

        Args:
            event: The close event.
        """
        self.shutdown_dials()
        self.settings_manager.save_settings(
            self.server_address,
            self.api_key,
            self.minimize_to_tray,
            self.start_in_tray,
            self.autostart_enabled,
        )
        self._save_assignments()
        event.accept()

    def resizeEvent(self, event: QEvent) -> None:
        """Enforce minimum window dimensions on resize.

        Args:
            event: The resize event.
        """
        new_size = event.size()
        if new_size.width() < WINDOW_RESIZE_MIN_WIDTH or new_size.height() < WINDOW_RESIZE_MIN_HEIGHT:
            self.resize(
                max(WINDOW_RESIZE_MIN_WIDTH, new_size.width()),
                max(WINDOW_RESIZE_MIN_HEIGHT, new_size.height()),
            )
        super().resizeEvent(event)

    def changeEvent(self, event: QEvent) -> None:
        """Minimize to tray when the window is minimized (if enabled).

        Args:
            event: The change event.
        """
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() == Qt.WindowState.WindowMinimized and self.minimize_to_tray:
                self.hide()
                self.tray_icon.show()
                event.ignore()
        super().changeEvent(event)

    # ── Tray Icon ─────────────────────────────────────────────────────

    def restore_window(self) -> None:
        """Restore the window from the system tray."""
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation events.

        Args:
            reason: The activation reason (single click, double click, etc.).
        """
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.restore_window()

    # ── Utility ───────────────────────────────────────────────────────

    def center_window(self) -> None:
        """Center the window on the primary screen."""
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def _set_autostart(self, enable: bool) -> None:
        """Configure Windows autostart via the registry.

        Args:
            enable: True to enable autostart, False to disable.
        """
        try:
            import winreg

            exe_path = sys.executable
            script_path = os.path.abspath(sys.argv[0])

            if exe_path.endswith("python.exe"):
                command = f'"{exe_path}" "{script_path}"'
            else:
                command = f'"{exe_path}"'

            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, AUTOSTART_REGISTRY_PATH, 0,
                    winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE,
                )
            except OSError:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, AUTOSTART_REGISTRY_PATH)

            if enable:
                winreg.SetValueEx(key, AUTOSTART_APP_NAME, 0, winreg.REG_SZ, command)
            else:
                try:
                    winreg.DeleteValue(key, AUTOSTART_APP_NAME)
                except OSError:
                    pass

            winreg.CloseKey(key)
            self.autostart_enabled = enable

        except Exception as e:
            logger.error("Error setting autostart: %s", e)
            QMessageBox.warning(self, "Error", f"Autostart could not be configured: {e}")

    def shutdown_dials(self) -> None:
        """Shut down all connected dials (set value to 0, turn off backlight)."""
        for dial_id in self.dial_widgets:
            self.api_client.shutdown_dial(dial_id)
