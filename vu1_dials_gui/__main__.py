"""
Entry point for running VU1 DIALs GUI as a Python package.

Usage:
    python -m vu1_dials_gui
"""

import logging
import sys

from PyQt6.QtWidgets import QApplication

from .main_window import VU1GUI


def main() -> None:
    """Initialize and run the VU1 DIALs GUI application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = VU1GUI()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
