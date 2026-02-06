"""
Application-wide constants and default values.

Centralizes all hardcoded values to make configuration and maintenance easier.
"""

import re

# --- Application Metadata ---
APP_NAME: str = "VU1 DIALs GUI"
APP_TITLE: str = "VU1 GUI"
HEADER_TITLE: str = "VU1 GUI Prototype"
WINDOW_TITLE: str = "VU1 GUI"
TRAY_TOOLTIP: str = "VU1 DIALs GUI"

# --- Window Dimensions ---
WINDOW_MIN_WIDTH: int = 935
WINDOW_MIN_HEIGHT: int = 600
WINDOW_DEFAULT_WIDTH: int = 935
WINDOW_DEFAULT_HEIGHT: int = 800
WINDOW_RESIZE_MIN_WIDTH: int = 800
WINDOW_RESIZE_MIN_HEIGHT: int = 600

# --- Dial Widget Dimensions ---
DIAL_WIDGET_WIDTH: int = 220
DIAL_IMAGE_WIDTH: int = 200
DIAL_IMAGE_HEIGHT: int = 144

# --- Server Defaults ---
DEFAULT_SERVER_ADDRESS: str = "http://localhost:5340"
DEFAULT_API_KEY: str = ""
API_BASE_PATH: str = "/api/v0"
REQUEST_TIMEOUT: int = 5
SHUTDOWN_TIMEOUT: int = 1

# --- API Endpoints (relative to API_BASE_PATH) ---
ENDPOINT_DIAL_LIST: str = "dial/list"
ENDPOINT_DIAL_IMAGE_GET: str = "dial/{dial_id}/image/get"
ENDPOINT_DIAL_IMAGE_SET: str = "dial/{dial_id}/image/set"
ENDPOINT_DIAL_STATUS: str = "dial/{dial_id}/status"
ENDPOINT_DIAL_SET: str = "dial/{dial_id}/set"
ENDPOINT_DIAL_NAME: str = "dial/{dial_id}/name"
ENDPOINT_DIAL_BACKLIGHT: str = "dial/{dial_id}/backlight"
ENDPOINT_DIAL_EASING: str = "dial/{dial_id}/easing/dial"

# --- Sensor Update ---
SENSOR_UPDATE_INTERVAL_MS: int = 1000

# --- RGB ---
RGB_MIN: int = 0
RGB_MAX: int = 255
RGB_API_MAX: int = 100

# --- Value Range ---
VALUE_RANGE_MIN: int = -999999
VALUE_RANGE_MAX: int = 999999
DEFAULT_MIN_VALUE: int = 0
DEFAULT_MAX_VALUE: int = 100

# --- Easing Defaults ---
DEFAULT_EASING_PERIOD: int = 50
DEFAULT_EASING_STEP: int = 5
EASING_PERIOD_MIN: int = 1
EASING_PERIOD_MAX: int = 1000
EASING_STEP_MIN: int = 1
EASING_STEP_MAX: int = 100

# --- Layout ---
FLOW_LAYOUT_SPACING_X: int = 10
FLOW_LAYOUT_SPACING_Y: int = 10
MAIN_LAYOUT_SPACING: int = 10
MAIN_LAYOUT_MARGIN: int = 10
HEADER_MAX_HEIGHT: int = 50

# --- Styling ---
HEADER_STYLE: str = "font-size: 18px; font-weight: bold;"
DIAL_ID_STYLE: str = "font-weight: bold;"

# --- File Names ---
SETTINGS_FILENAME: str = "settings.json"
ASSIGNMENTS_FILENAME: str = "assignments.json"
ICON_FILENAME: str = "icon.png"

# --- Image File Filter ---
IMAGE_FILE_FILTER: str = "Pictures (*.png *.jpg *.jpeg)"
SUPPORTED_IMAGE_EXTENSIONS: tuple[str, ...] = (".png", ".jpg", ".jpeg")

# --- Windows Autostart ---
AUTOSTART_REGISTRY_PATH: str = r"Software\Microsoft\Windows\CurrentVersion\Run"
AUTOSTART_APP_NAME: str = "VU1_DIALS_GUI"

# --- API Authentication ---
API_KEY_HEADER: str = "X-API-Key"

# --- Input Validation ---
DIAL_NAME_MAX_LENGTH: int = 64
# Allow letters (unicode), digits, spaces, hyphens, underscores, dots
DIAL_NAME_PATTERN: re.Pattern = re.compile(r"[^\w\s\-.]", re.UNICODE)
SERVER_ADDRESS_SCHEMES: tuple[str, ...] = ("http", "https")
