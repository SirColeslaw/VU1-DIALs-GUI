import sys
import os
import json
import requests
import winreg
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QPushButton, QLineEdit, QComboBox, QCheckBox,
    QSpinBox, QColorDialog, QFileDialog, QMessageBox, QDialog, QFrame, QLayout,
    QSystemTrayIcon, QMenu, QStyle)
from PyQt6.QtCore import Qt, QTimer, QSize, QRect, QPoint, QEvent, QObject
from PyQt6.QtGui import QImage, QPixmap, QColor, QAction, QIcon
from PIL import Image
from io import BytesIO
from python_aida64 import getData

class DialWidget(QFrame):
    def __init__(self, parent=None, dial_id=None):
        super().__init__(parent)
        self.dial_id = dial_id
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.layout = QVBoxLayout(self)
        self.setFixedWidth(220)
        self.setup_ui()

    def setup_ui(self):
        # ID Label
        self.id_label = QLabel(f"Dial ID: {self.dial_id}")
        self.id_label.setStyleSheet("font-weight: bold;")
        self.layout.addWidget(self.id_label)

        # Image Label
        self.image_label = QLabel()
        self.image_label.setFixedSize(200, 144)
        self.layout.addWidget(self.image_label)

        # Set Image Button
        self.set_image_btn = QPushButton("Set Image")
        self.layout.addWidget(self.set_image_btn)

        # Name Field
        self.name_label = QLabel("Name:")
        self.name_input = QLineEdit()
        self.save_name_btn = QPushButton("Save Name")
        self.layout.addWidget(self.name_label)
        self.layout.addWidget(self.name_input)
        self.layout.addWidget(self.save_name_btn)

        # Backlight Controls
        backlight_frame = QFrame()
        backlight_layout = QVBoxLayout(backlight_frame)
        
        rgb_layout = QHBoxLayout()
        self.red_spin = QSpinBox()
        self.green_spin = QSpinBox()
        self.blue_spin = QSpinBox()
        for spin in [self.red_spin, self.green_spin, self.blue_spin]:
            spin.setRange(0, 255)
            rgb_layout.addWidget(spin)
        
        self.color_picker_btn = QPushButton("Pick Color")
        self.save_backlight_btn = QPushButton("Set Backlight")
        
        backlight_layout.addLayout(rgb_layout)
        backlight_layout.addWidget(self.color_picker_btn)
        backlight_layout.addWidget(self.save_backlight_btn)
        self.layout.addWidget(backlight_frame)

        # Sensor Selection
        self.sensor_combo = QComboBox()
        self.assign_sensor_btn = QPushButton("Assign Sensor")
        self.layout.addWidget(QLabel("AIDA64 Sensor:"))
        self.layout.addWidget(self.sensor_combo)
        self.layout.addWidget(self.assign_sensor_btn)

        # Value Range
        range_frame = QFrame()
        range_layout = QVBoxLayout(range_frame)
        self.min_value = QSpinBox()
        self.max_value = QSpinBox()
        self.min_value.setRange(-999999, 999999)
        self.max_value.setRange(-999999, 999999)
        range_layout.addWidget(QLabel("Min Value:"))
        range_layout.addWidget(self.min_value)
        range_layout.addWidget(QLabel("Max Value:"))
        range_layout.addWidget(self.max_value)
        self.save_range_btn = QPushButton("Save Range")
        range_layout.addWidget(self.save_range_btn)
        self.layout.addWidget(range_frame)

        # Easing Controls
        easing_frame = QFrame()
        easing_layout = QVBoxLayout(easing_frame)
        
        # Period Control
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("Update Period (ms):"))
        self.period_spin = QSpinBox()
        self.period_spin.setRange(1, 1000)
        self.period_spin.setValue(50)  # Default Wert
        period_layout.addWidget(self.period_spin)
        easing_layout.addLayout(period_layout)
        
        # Step Control
        step_layout = QHBoxLayout()
        step_layout.addWidget(QLabel("Max Step (%):"))
        self.step_spin = QSpinBox()
        self.step_spin.setRange(1, 100)
        self.step_spin.setValue(5)  # Default Wert
        step_layout.addWidget(self.step_spin)
        easing_layout.addLayout(step_layout)
        
        # Save Easing Button
        self.save_easing_btn = QPushButton("Save Easing")
        easing_layout.addWidget(self.save_easing_btn)
        
        self.layout.addWidget(easing_frame)

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        layout = QVBoxLayout(self)

        # Server Address
        self.server_input = QLineEdit()
        layout.addWidget(QLabel("Server Address:"))
        layout.addWidget(self.server_input)

        # API Key
        self.api_key_input = QLineEdit()
        layout.addWidget(QLabel("API Key:"))
        layout.addWidget(self.api_key_input)
        
        # Minimize to Tray Option
        self.minimize_to_tray = QCheckBox("Minimize to Tray")
        layout.addWidget(self.minimize_to_tray)

        # Autostart Option
        self.autostart = QCheckBox("Start with Windows")
        layout.addWidget(self.autostart)

        # Start in Tray Option
        self.start_in_tray = QCheckBox("Start minimized to Tray")
        layout.addWidget(self.start_in_tray)

        # Save Button
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.accept)
        layout.addWidget(self.save_btn)

class FlowLayout(QLayout):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._items = []
        self._rows = [] 

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, index):
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientation(0)  

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        space_x = 10
        space_y = 10
        self._rows = []
        current_row = []

        for item in self._items:
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                self._rows.append(current_row)
                current_row = []
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())
            current_row.append(item)

        if current_row:
            self._rows.append(current_row)

        return y + line_height

class VU1GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Connect to QApplication's aboutToQuit signal
        QApplication.instance().aboutToQuit.connect(self.shutdown_dials)
        
        # Get the correct base path whether running as script or exe
        if getattr(sys, 'frozen', False):
            # Running as exe
            self.base_path = os.path.dirname(sys.executable)
        else:
            # Running as script
            self.base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Load settings from JSON file with correct path
        self.settings_file = os.path.join(self.base_path, "settings.json")
        self.assignments_file = os.path.join(self.base_path, "assignments.json")
        
        self.settings = self.load_settings()
        
        # Initialize settings with default values but prefer loaded settings
        self.autostart_enabled = self.settings.get("autostart", False)
        self.minimize_to_tray = self.settings.get("minimize_to_tray", False)
        self.start_in_tray = self.settings.get("start_in_tray", False)
        self.server_address = self.settings.get("server_address", "http://localhost:5340")  # Set default server address
        self.api_key = self.settings.get("api_key", "")  # Changed to empty string
        self.backlight_values = {}  # Initialize backlight_values
        
        # Basic window setup
        self.setWindowTitle("VU1 GUI")
        self.setMinimumSize(935, 600)
        self.resize(935, 800)
        self.center_window()
        
        # If no server address or API key is set, show settings dialog
        if not self.server_address or not self.api_key:
            self._show_settings_dialog()
        
        # Widgets and data
        self.dial_widgets = {}
        self.sensor_assignments = {}
        self.min_values = {}
        self.max_values = {}
        
        # GUI setup
        self.setup_ui()
        
        # Initial fetch of AIDA64 data
        self.statusBar().showMessage("Load AIDA64 Sensor data...")
        self.aida64_data = self.fetch_aida64_data()  # Get initial sensor data
        
        # Load assignments from JSON file
        self.load_assignments()
        
        # Timer for sensor updates
        self.update_timer = QTimer()
        self.update_timer.setInterval(1000)
        self.update_timer.timeout.connect(self.schedule_sensor_updates)
        
        # Fetch all dial details
        self.fetch_all_dial_details()
        self.update_timer.start()
        
        self.statusBar().showMessage("Ready")
        
        # Tray Icon Setup
        self.tray_icon = QSystemTrayIcon(self)
        icon = QIcon("icon.png") if os.path.exists("icon.png") else self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("VU1 DIALs GUI")
        
        # Only double-clicking the tray icon will restore the window
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # Load minimize to tray setting
        self.minimize_to_tray = self.settings.get("minimize_to_tray", False)

        # If start in tray is enabled, hide the window and show the tray icon
        if self.start_in_tray:
            self.hide()
            self.tray_icon.show()
        else:
            self.show()

    def load_settings(self):
        """Loads the settings from the JSON file"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, "r") as file:
                    settings = json.load(file)
                    # Validate required settings
                    if not settings.get("server_address") or not settings.get("api_key"):
                        return {}
                    return settings
            return {}
        except Exception as e:
            print(f"Error loading settings: {e}")
            return {}

    def save_settings(self):
        """Saves the current settings to the JSON file"""
        try:
            settings = {
                "server_address": self.server_address,
                "api_key": self.api_key,
                "minimize_to_tray": self.minimize_to_tray,
                "start_in_tray": self.start_in_tray,  # Neue Option
                "autostart": self.autostart_enabled
            }
            
            with open(self.settings_file, "w") as f:
                json.dump(settings, f, indent=4)
                
        except Exception as e:
            print(f"Error saving settings: {e}")
            QMessageBox.warning(self, "Error", 
                              "The settings could not be saved.")

    def closeEvent(self, event):
        """Called when the window is closed"""
        # First shutdown the dials
        self.shutdown_dials()
        # Then save the settings and assignments
        self.save_settings()
        self.save_assignments()
        event.accept()

    def setup_ui(self):
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Main layout
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header.setMaximumHeight(50)
        
        title = QLabel("VU1 GUI Prototype")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        settings_btn = QPushButton("Settings")
        settings_btn.clicked.connect(self._show_settings_dialog)
        header_layout.addWidget(title)
        header_layout.addStretch()  # Adds spacing between title and button
        header_layout.addWidget(settings_btn)
        main_layout.addWidget(header)
        
        # Add container for dials directly
        self.dials_container = QWidget()
        self.dials_layout = FlowLayout(self.dials_container)
        self.dials_container.setLayout(self.dials_layout)
        main_layout.addWidget(self.dials_container)
        
        # Status Bar
        self.statusBar().showMessage("Ready")

    def create_dial_widget(self, details, dial_id):
        """Create or update a dial widget"""
        try:
            # Remove existing widget if it exists
            if dial_id in self.dial_widgets:
                old_widget = self.dial_widgets[dial_id]
                self.dials_layout.removeWidget(old_widget)
                old_widget.deleteLater()

            # Create new widget
            widget = DialWidget(dial_id=dial_id)
            self.dial_widgets[dial_id] = widget
            
            # Signal connections
            widget.set_image_btn.clicked.connect(
                lambda: self.set_image_for_dial(dial_id))
            widget.save_name_btn.clicked.connect(
                lambda: self.set_dial_name(dial_id, widget.name_input.text()))
            widget.color_picker_btn.clicked.connect(
                lambda: self.show_color_picker(dial_id))
            widget.save_backlight_btn.clicked.connect(
                lambda: self.set_backlight(dial_id, widget.red_spin.value(),
                                         widget.green_spin.value(), 
                                         widget.blue_spin.value()))
            widget.assign_sensor_btn.clicked.connect(
                lambda: self.assign_sensor_to_dial(dial_id, 
                                                 widget.sensor_combo.currentText()))
            widget.save_range_btn.clicked.connect(
                lambda: self.set_value_range(dial_id, widget.min_value.value(),
                                           widget.max_value.value()))
            widget.save_easing_btn.clicked.connect(
                lambda: self.set_dial_easing(dial_id, 
                                           widget.period_spin.value(),
                                           widget.step_spin.value()))

            # Update widget with data
            self.update_dial_widget_with_data(widget, details)
            
            # Add widget to layout
            self.dials_layout.addWidget(widget)
            
            # Restore the stored backlight levels
            if dial_id in self.backlight_values:
                saved_backlight = self.backlight_values[dial_id]
                widget.red_spin.setValue(saved_backlight["red"])
                widget.green_spin.setValue(saved_backlight["green"])
                widget.blue_spin.setValue(saved_backlight["blue"])
                self.set_backlight(dial_id, 
                                saved_backlight["red"],
                                saved_backlight["green"],
                                saved_backlight["blue"])
            
            # Customize window size
            self.adjustSize()
            
        except Exception as e:
            print(f"Error creating widget for Dial {dial_id}: {e}")

    def show_color_picker(self, dial_id):
        color = QColorDialog.getColor()
        if color.isValid():
            widget = self.dial_widgets[dial_id]
            widget.red_spin.setValue(color.red())
            widget.green_spin.setValue(color.green())
            widget.blue_spin.setValue(color.blue())

    def _show_settings_dialog(self):
        dialog = SettingsDialog(self)
        dialog.server_input.setText(self.server_address)
        dialog.api_key_input.setText(self.api_key)
        dialog.minimize_to_tray.setChecked(self.minimize_to_tray)
        dialog.autostart.setChecked(self.autostart_enabled)
        dialog.start_in_tray.setChecked(self.start_in_tray)
        
        if dialog.exec():
            # Check if API key has been entered
            if not dialog.api_key_input.text().strip():
                QMessageBox.critical(self, "Error",
                                  "No API key was provided!\n"
                                  "Please enter a valid API key.",
                                  QMessageBox.StandardButton.Ok)
                self._show_settings_dialog()
                return
            
            # Check if server is available
            try:
                test_url = f"{dialog.server_input.text().strip()}/api/v0/dial/list"
                response = requests.get(test_url, params={"key": dialog.api_key_input.text()}, timeout=5)
                response.raise_for_status()
            except (requests.ConnectionError, requests.Timeout):
                QMessageBox.critical(self, "Fehler",
                                  f"The server at {dialog.server_input.text()} is unavailable!\n"
                                  "Please check the server address and your network connection.",
                                  QMessageBox.StandardButton.Ok)
                self._show_settings_dialog()
                return
            except requests.RequestException as e:
                QMessageBox.critical(self, "Error",
                                  f"Error connecting to the server: {str(e)}",
                                  QMessageBox.StandardButton.Ok)
                self._show_settings_dialog()
                return
            
            # If all checks are successful, save the settings.
            self.server_address = dialog.server_input.text()
            self.api_key = dialog.api_key_input.text()
            self.minimize_to_tray = dialog.minimize_to_tray.isChecked()
            self.start_in_tray = dialog.start_in_tray.isChecked()
            
            if dialog.autostart.isChecked() != self.autostart_enabled:
                self.set_autostart(dialog.autostart.isChecked())
            
            self.save_settings()

    def schedule_sensor_updates(self):
        """Periodically updates the sensor data"""
        self.aida64_data = self.fetch_aida64_data()
        self.update_all_dials()

    def update_all_dials(self):
        """Update all dials with the latest sensor data"""
        for dial_id in self.sensor_assignments:
            self.update_dial_with_sensor_data(dial_id)

    def update_dial_with_sensor_data(self, dial_id):
        """Updates a single dial with sensor data"""
        try:
            sensor = self.sensor_assignments.get(dial_id)
            if not sensor:
                return

            sensor_id = sensor.split('(')[-1].strip(')')
            # Search in all categories for the sensor
            sensor_data = None
            for category in self.aida64_data.values():
                if isinstance(category, list):
                    found = next((item for item in category if item['id'] == sensor_id), None)
                    if found:
                        sensor_data = found
                        break
            
            if sensor_data and 'value' in sensor_data:
                value = float(sensor_data['value'])
                min_value = self.min_values.get(dial_id, 0)
                max_value = self.max_values.get(dial_id, 100)
                mapped_value = self.map_value_to_range(value, min_value, max_value)
                self.set_dial_value(dial_id, mapped_value)
        except Exception as e:
            print(f"Error updating Dial {dial_id}: {e}")

    def fetch_aida64_data(self):
        """Get the latest AIDA64 data"""
        try:
            return getData()
        except Exception as e:
            print(f"Error retrieving AIDA64 data: {e}")
            return {}

    def map_value_to_range(self, value, min_value, max_value):
        """Maps a value to the range 0-100"""
        try:
            return max(0, min(100, ((value - min_value) / (max_value - min_value)) * 100))
        except (ZeroDivisionError, TypeError):
            return 0

    def set_dial_value(self, dial_id, value):
        """Set the value of a dial using the API"""
        try:
            url = f"{self.server_address}/api/v0/dial/{dial_id}/set"
            params = {"key": self.api_key, "value": value}
            response = requests.get(url, params=params)
            response.raise_for_status()
        except Exception as e:
            print(f"Error setting the dial value {dial_id}: {e}")

    def load_assignments(self):
        """Loads the sensor assignments, value ranges and backlight settings"""
        try:
            if os.path.exists(self.assignments_file):
                with open(self.assignments_file, "r") as file:
                    data = json.load(file)
                    self.sensor_assignments = data.get("sensor_assignments", {})
                    self.min_values = data.get("min_values", {})
                    self.max_values = data.get("max_values", {})
                    self.backlight_values = data.get("backlight_values", {})
            self.statusBar().showMessage("Settings and assignments loaded")
        except Exception as e:
            print(f"Error loading assignments: {e}")
            self.sensor_assignments = {}
            self.min_values = {}
            self.max_values = {}
            self.backlight_values = {}
            self.statusBar().showMessage("Error loading settings!")

    def save_assignments(self):
        """Saves the sensor assignments, value ranges and backlight settings"""
        try:
            # Collect current backlight values
            for dial_id, widget in self.dial_widgets.items():
                self.backlight_values[dial_id] = {
                    "red": widget.red_spin.value(),
                    "green": widget.green_spin.value(),
                    "blue": widget.blue_spin.value()
                }
            
            data = {
                "sensor_assignments": self.sensor_assignments,
                "min_values": self.min_values,
                "max_values": self.max_values,
                "backlight_values": self.backlight_values  # Add backlight values
            }
            with open(self.assignments_file, "w") as file:
                json.dump(data, file, indent=4)
            self.statusBar().showMessage("Settings and assignments saved")
        except Exception as e:
            print(f"Error when saving assignments: {e}")
            QMessageBox.warning(self, "Error", 
                              "The assignments could not be saved.")

    def update_dial_widget_with_data(self, widget, details):
        """Refreshes the widget display with the details"""
        try:
            status_data = details.get("status", {}).get("data", {})
            
            # update name
            name = status_data.get("dial_name", "")
            widget.name_input.setText(name)

            # No longer get the backlight values from the API,
            # instead, they are loaded from assignments.json

            # refresh this image
            if "image" in details and details["image"]:
                image = QImage.fromData(details["image"])
                if not image.isNull():
                    scaled_pixmap = QPixmap.fromImage(image).scaled(
                        widget.image_label.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    widget.image_label.setPixmap(scaled_pixmap)

            # Set min/max values from local settings
            widget.min_value.setValue(int(float(self.min_values.get(widget.dial_id, 0))))
            widget.max_value.setValue(int(float(self.max_values.get(widget.dial_id, 100))))

            # Update sensor combo box
            if self.aida64_data:
                widget.sensor_combo.clear()
                sensor_options = []
                # Search all categories for sensors
                for category in self.aida64_data.values():
                    if isinstance(category, list):
                        for item in category:
                            if 'label' in item and 'id' in item:
                                sensor_options.append(f"{item['label']} ({item['id']})")
                
                widget.sensor_combo.addItems(sorted(sensor_options))  # Sort the list alphabetically.
                
                # Set selected sensor
                if widget.dial_id in self.sensor_assignments:
                    index = widget.sensor_combo.findText(
                        self.sensor_assignments[widget.dial_id])
                    if index >= 0:
                        widget.sensor_combo.setCurrentIndex(index)

            # Update easing parameters
            easing = status_data.get("easing", {})
            if easing:
                widget.period_spin.setValue(int(easing.get("dial_period", 50)))
                widget.step_spin.setValue(int(easing.get("dial_step", 5)))

        except Exception as e:
            print(f"Error updating widget: {e}")

    def fetch_all_dial_details(self):
        """Get the details of all available dials"""
        try:
            url = f"{self.server_address}/api/v0/dial/list"
            params = {"key": self.api_key}
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            response_data = response.json()
            
            dials = response_data.get("data", [])
            if not isinstance(dials, list):
                raise ValueError(f"Invalid API response format: {response_data}")
            
            # Delete existing widgets
            for widget in self.dial_widgets.values():
                widget.deleteLater()
            self.dial_widgets.clear()
            
            # Create new widgets for each dial
            for dial in dials:
                details = self.fetch_dial_details(dial['uid'])
                self.create_dial_widget(details, dial['uid'])
                
            # After creating all widgets, adjust the window size
            self.adjustSize()
            # Center the window on the screen
            self.center_window()
                
        except Exception as e:
            print(f"Error retrieving dial list: {e}")
            QMessageBox.warning(self, "Error", 
                              f"Error retrieving the dials: {str(e)}")

    def center_window(self):
        """Centers the window on the screen"""
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)

    def fetch_dial_details(self, dial_id):
        """Get the details for a single call"""
        details = {}
        endpoints = {
            "image": f"dial/{dial_id}/image/get",
            "status": f"dial/{dial_id}/status"  # Range endpoint removed
        }
        
        try:
            for key, endpoint in endpoints.items():
                url = f"{self.server_address}/api/v0/{endpoint}"
                params = {"key": self.api_key}
                
                headers = {}
                if key != "image":
                    headers["Accept"] = "application/json"
                
                response = requests.get(url, params=params, headers=headers)
                response.raise_for_status()
                
                if key == "image":
                    if response.headers.get('Content-Type') == 'image/png':
                        details[key] = response.content
                    else:
                        details[key] = None
                else:
                    details[key] = response.json()
                    
        except Exception as e:
            print(f"Error retrieving details for Dial {dial_id}: {e}")
            details[key] = None
            
        return details

    def set_image_for_dial(self, dial_id):
        """Sets a new image for a dial"""
        try:
            file_path = QFileDialog.getOpenFileName(
                self, 
                "Select an image",
                "",
                "Pictures (*.png *.jpg *.jpeg)"
            )[0]
            
            if not file_path:
                return
                
            if not file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                QMessageBox.warning(self, "Error", 
                                  "Please select a PNG or JPG file.")
                return
            
            url = f"{self.server_address}/api/v0/dial/{dial_id}/image/set"
            params = {"key": self.api_key}
            
            with open(file_path, "rb") as image_file:
                files = {"imgfile": image_file}
                response = requests.post(url, params=params, files=files)
                response.raise_for_status()
            
            # Update the widget with the new details
            details = self.fetch_dial_details(dial_id)
            self.update_dial_widget_with_data(self.dial_widgets[dial_id], details)
            
            # Add status message
            self.statusBar().showMessage(f"New image for Dial {dial_id} set: {os.path.basename(file_path)}")
            
        except Exception as e:
            print(f"Error setting image for dial {dial_id}: {e}")
            QMessageBox.warning(self, "Error", 
                              f"Error setting image: {str(e)}")

    def set_dial_name(self, dial_id, new_name):
        """Sets a new name for a dialog"""
        try:
            url = f"{self.server_address}/api/v0/dial/{dial_id}/name"
            params = {"key": self.api_key, "name": new_name}
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Aktualisiere das Widget
            details = self.fetch_dial_details(dial_id)
            self.update_dial_widget_with_data(self.dial_widgets[dial_id], details)
            
            # Statusmeldung hinzufügen
            self.statusBar().showMessage(f"Name for dial {dial_id} has been set to '{new_name}'")
            
        except Exception as e:
            print(f"Error setting name for dial {dial_id}: {e}")
            QMessageBox.warning(self, "Error", 
                              f"Error setting name: {str(e)}")

    def set_backlight(self, dial_id, red, green, blue):
        """Sets the background color of a dialog"""
        try:
            # Convert RGB (0-255) to percentage values (0-100)
            red_pct = int((red / 255) * 100)
            green_pct = int((green / 255) * 100)
            blue_pct = int((blue / 255) * 100)
            
            url = f"{self.server_address}/api/v0/dial/{dial_id}/backlight"
            params = {
                "key": self.api_key,
                "red": red_pct,
                "green": green_pct,
                "blue": blue_pct
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Speichere die aktuellen Werte
            self.backlight_values[dial_id] = {
                "red": red,
                "green": green,
                "blue": blue
            }
            
            # Statusmeldung hinzufügen
            self.statusBar().showMessage(f"Backlight for dial {dial_id} set to RGB({red}, {green}, {blue})")
            
        except Exception as e:
            print(f"Error setting background color for Dial {dial_id}: {e}")
            QMessageBox.warning(self, "Error", 
                              f"Error setting background color: {str(e)}")

    def assign_sensor_to_dial(self, dial_id, sensor_text):
        """Assign an AIDA64 sensor to a dial"""
        try:
            if not sensor_text:
                return
            
            self.sensor_assignments[dial_id] = sensor_text
            self.save_assignments()
            
            # Aktualisiere sofort den Wert
            self.update_dial_with_sensor_data(dial_id)
            
            # Statusmeldung hinzufügen
            sensor_name = sensor_text.split(" (")[0]  # Extrahiere den lesbaren Namen
            self.statusBar().showMessage(f"Sensor '{sensor_name}' Dial {dial_id} assigned")
            
        except Exception as e:
            print(f"Error assigning sensor for dial {dial_id}: {e}")
            QMessageBox.warning(self, "Error", 
                              f"Error assigning sensor: {str(e)}")

    def set_value_range(self, dial_id, min_value, max_value):
        """Saves the value range for a dial"""
        try:
            # Convert to integer before saving
            self.min_values[dial_id] = int(min_value)
            self.max_values[dial_id] = int(max_value)
            self.save_assignments()
            
            # Update the value immediately
            self.update_dial_with_sensor_data(dial_id)
            
            # Add status message
            self.statusBar().showMessage(f"Value range for dialog {dial_id} set to {min_value} - {max_value}")
            
        except Exception as e:
            print(f"Error setting the value range for Dial {dial_id}: {e}")
            QMessageBox.warning(self, "Error", 
                              f"Error setting the value range: {str(e)}")

    def set_dial_easing(self, dial_id, period, step):
        """Sets the easing parameters of a dial"""
        try:
            url = f"{self.server_address}/api/v0/dial/{dial_id}/easing/dial"
            params = {
                "key": self.api_key,
                "period": period,
                "step": step
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            self.statusBar().showMessage(f"Easing parameter for dialog {dial_id} updated")
            
        except Exception as e:
            print(f"Error setting easing parameters for dial {dial_id}: {e}")
            QMessageBox.warning(self, "Error", 
                              f"Error setting the easing parameters: {str(e)}")

    def resizeEvent(self, event):
        """Override resizeEvent to enforce minimum size"""
        new_size = event.size()
        if new_size.width() < 800 or new_size.height() < 600:
            self.resize(max(800, new_size.width()), 
                       max(600, new_size.height()))
        super().resizeEvent(event)

    def update_layout(self):
        """Refreshes the layout and window size"""
        try:
            self.adjustSize()
        except Exception as e:
            print(f"Error updating the layout: {e}")
            self.statusBar().showMessage(f"Error during layout update: {str(e)}")

    def changeEvent(self, event):
        """Called when the window state changes"""
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() == Qt.WindowState.WindowMinimized and self.minimize_to_tray:
                self.hide()
                self.tray_icon.show()
                event.ignore()
        super().changeEvent(event)

    def restore_window(self):
        """Restore the window from the tray"""
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def tray_icon_activated(self, reason):
        """Handles clicks on the tray icon"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.restore_window()

    def set_autostart(self, enable):
        """Activates or deactivates the autorun function"""
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            app_name = "VU1_DIALS_GUI"
            exe_path = sys.executable
            script_path = os.path.abspath(sys.argv[0])
            
            # When the app runs as a Python script
            if exe_path.endswith("python.exe"):
                command = f'"{exe_path}" "{script_path}"'
            else:
                # When the app is compiled as an EXE
                command = f'"{exe_path}"'

            try:
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, 
                                   winreg.KEY_SET_VALUE | winreg.KEY_QUERY_VALUE)
            except WindowsError:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)

            if enable:
                winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, command)
            else:
                try:
                    winreg.DeleteValue(key, app_name)
                except WindowsError:
                    pass

            winreg.CloseKey(key)
            self.autostart_enabled = enable
            
        except Exception as e:
            print(f"Error setting autostart: {e}")
            QMessageBox.warning(self, "Error", 
                              f"Autostart could not be configured: {str(e)}")

    def shutdown_dials(self):
        """Set all dials to 0 and turn off the light."""
        try:
            for dial_id in self.dial_widgets.keys():
                try:
                    # Set value to 0
                    url = f"{self.server_address}/api/v0/dial/{dial_id}/set"
                    params = {"key": self.api_key, "value": 0}
                    requests.get(url, params=params, timeout=1)
                    
                    # Turn off backlight
                    url = f"{self.server_address}/api/v0/dial/{dial_id}/backlight"
                    params = {
                        "key": self.api_key,
                        "red": 0,
                        "green": 0,
                        "blue": 0
                    }
                    requests.get(url, params=params, timeout=1)
                except requests.exceptions.Timeout:
                    continue  # Skip to next dial if timeout occurs
                except Exception as e:
                    print(f"Error shutting down dial {dial_id}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error when shutting down the dials: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    window = VU1GUI()
    # window.show() has been moved to the __init__ method
    sys.exit(app.exec())

