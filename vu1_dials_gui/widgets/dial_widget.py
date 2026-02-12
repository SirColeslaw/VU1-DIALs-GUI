"""
Dial widget for displaying and controlling a single VU1 dial.

Provides controls for image display, name, RGB backlight,
AIDA64 sensor assignment, value range, and easing parameters.
"""

from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..constants import (
    DEFAULT_EASING_PERIOD,
    DEFAULT_EASING_STEP,
    DIAL_ID_STYLE,
    DIAL_IMAGE_HEIGHT,
    DIAL_IMAGE_WIDTH,
    DIAL_WIDGET_WIDTH,
    EASING_PERIOD_MAX,
    EASING_PERIOD_MIN,
    EASING_STEP_MAX,
    EASING_STEP_MIN,
    RGB_MAX,
    RGB_MIN,
    VALUE_RANGE_MAX,
    VALUE_RANGE_MIN,
)


class DialWidget(QFrame):
    """Widget representing a single VU1 dial with all its controls.

    Displays the dial image and provides UI controls for name,
    backlight color, sensor assignment, value range, and easing.
    """

    def __init__(self, parent: QWidget | None = None, dial_id: str | None = None) -> None:
        """Initialize the dial widget.

        Args:
            parent: Parent widget.
            dial_id: Unique identifier of the dial this widget controls.
        """
        super().__init__(parent)
        self.dial_id: str | None = dial_id
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.main_layout = QVBoxLayout(self)
        self.setFixedWidth(DIAL_WIDGET_WIDTH)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Build all UI elements for the dial widget."""
        self._setup_id_label()
        self._setup_image()
        self._setup_name_controls()
        self._setup_backlight_controls()
        self._setup_sensor_controls()
        self._setup_range_controls()
        self._setup_easing_controls()

    def _setup_id_label(self) -> None:
        """Create the dial ID label."""
        self.id_label = QLabel(f"Dial ID: {self.dial_id}")
        self.id_label.setStyleSheet(DIAL_ID_STYLE)
        self.main_layout.addWidget(self.id_label)

    def _setup_image(self) -> None:
        """Create the image display area and set-image button."""
        self.image_label = QLabel()
        self.image_label.setFixedSize(DIAL_IMAGE_WIDTH, DIAL_IMAGE_HEIGHT)
        self.main_layout.addWidget(self.image_label)

        self.set_image_btn = QPushButton("Set Image")
        self.main_layout.addWidget(self.set_image_btn)

    def _setup_name_controls(self) -> None:
        """Create name input field and save button."""
        self.name_label = QLabel("Name:")
        self.name_input = QLineEdit()
        self.save_name_btn = QPushButton("Save Name")
        self.main_layout.addWidget(self.name_label)
        self.main_layout.addWidget(self.name_input)
        self.main_layout.addWidget(self.save_name_btn)

    def _setup_backlight_controls(self) -> None:
        """Create RGB backlight sliders, color picker, and set button."""
        backlight_frame = QFrame()
        backlight_layout = QVBoxLayout(backlight_frame)

        rgb_layout = QHBoxLayout()
        self.red_spin = QSpinBox()
        self.green_spin = QSpinBox()
        self.blue_spin = QSpinBox()
        for spin in [self.red_spin, self.green_spin, self.blue_spin]:
            spin.setRange(RGB_MIN, RGB_MAX)
            rgb_layout.addWidget(spin)

        self.color_picker_btn = QPushButton("Pick Color")
        self.save_backlight_btn = QPushButton("Set Backlight")

        backlight_layout.addLayout(rgb_layout)
        backlight_layout.addWidget(self.color_picker_btn)
        backlight_layout.addWidget(self.save_backlight_btn)
        self.main_layout.addWidget(backlight_frame)

    def _setup_sensor_controls(self) -> None:
        """Create AIDA64 sensor dropdown and assign button."""
        self.sensor_combo = QComboBox()
        self.assign_sensor_btn = QPushButton("Assign Sensor")
        self.main_layout.addWidget(QLabel("AIDA64 Sensor:"))
        self.main_layout.addWidget(self.sensor_combo)
        self.main_layout.addWidget(self.assign_sensor_btn)

    def _setup_range_controls(self) -> None:
        """Create min/max value range inputs and save button."""
        range_frame = QFrame()
        range_layout = QVBoxLayout(range_frame)
        self.min_value = QSpinBox()
        self.max_value = QSpinBox()
        self.min_value.setRange(VALUE_RANGE_MIN, VALUE_RANGE_MAX)
        self.max_value.setRange(VALUE_RANGE_MIN, VALUE_RANGE_MAX)
        range_layout.addWidget(QLabel("Min Value:"))
        range_layout.addWidget(self.min_value)
        range_layout.addWidget(QLabel("Max Value:"))
        range_layout.addWidget(self.max_value)
        self.save_range_btn = QPushButton("Save Range")
        range_layout.addWidget(self.save_range_btn)
        self.main_layout.addWidget(range_frame)

    def _setup_easing_controls(self) -> None:
        """Create easing period/step inputs and save button.

        Easing controls how smoothly the physical dial needle moves to a
        new value instead of jumping instantly.  The VU1 Server firmware
        interpolates between the current and target position using two
        parameters:

        - **Period** (ms): How often the firmware advances the needle
          toward the target.  Lower values = faster updates.
        - **Step** (%): The maximum percentage the needle may move in a
          single period tick.  Lower values = smoother but slower motion.

        Example: period=50, step=5 → the needle moves at most 5% every
        50 ms, taking up to 1 second to traverse the full 0–100 range.
        """
        easing_frame = QFrame()
        easing_layout = QVBoxLayout(easing_frame)

        # Period: interval between firmware interpolation ticks (ms)
        period_layout = QHBoxLayout()
        period_layout.addWidget(QLabel("Update Period (ms):"))
        self.period_spin = QSpinBox()
        self.period_spin.setRange(EASING_PERIOD_MIN, EASING_PERIOD_MAX)
        self.period_spin.setValue(DEFAULT_EASING_PERIOD)
        period_layout.addWidget(self.period_spin)
        easing_layout.addLayout(period_layout)

        # Step: max needle travel per tick (% of full range)
        step_layout = QHBoxLayout()
        step_layout.addWidget(QLabel("Max Step (%):"))
        self.step_spin = QSpinBox()
        self.step_spin.setRange(EASING_STEP_MIN, EASING_STEP_MAX)
        self.step_spin.setValue(DEFAULT_EASING_STEP)
        step_layout.addWidget(self.step_spin)
        easing_layout.addLayout(step_layout)

        self.save_easing_btn = QPushButton("Save Easing")
        easing_layout.addWidget(self.save_easing_btn)

        self.main_layout.addWidget(easing_frame)
