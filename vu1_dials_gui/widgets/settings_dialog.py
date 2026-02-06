"""
Settings dialog for configuring application preferences.

Provides a modal dialog for editing server connection,
tray behavior, and autostart settings.
"""

from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class SettingsDialog(QDialog):
    """Modal dialog for editing application settings.

    Allows the user to configure server address, API key,
    minimize-to-tray behavior, autostart, and start-minimized options.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the settings dialog.

        Args:
            parent: Parent widget for the dialog.
        """
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
