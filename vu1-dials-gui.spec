# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for VU1 DIALs GUI.

Builds a single-file Windows executable with all dependencies bundled.
Usage (on Windows):
    pip install pyinstaller
    pyinstaller vu1-dials-gui.spec
"""

import sys
from pathlib import Path

block_cipher = None

# Collect the package data
a = Analysis(
    ['vu1-dials-gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Include icon if present
        *([('icon.png', '.')] if Path('icon.png').exists() else []),
    ],
    hiddenimports=[
        'vu1_dials_gui',
        'vu1_dials_gui.__main__',
        'vu1_dials_gui.main_window',
        'vu1_dials_gui.constants',
        'vu1_dials_gui.platform',
        'vu1_dials_gui.utils',
        'vu1_dials_gui.validation',
        'vu1_dials_gui.api',
        'vu1_dials_gui.api.client',
        'vu1_dials_gui.config',
        'vu1_dials_gui.config.crypto',
        'vu1_dials_gui.config.settings',
        'vu1_dials_gui.widgets',
        'vu1_dials_gui.widgets.dial_widget',
        'vu1_dials_gui.widgets.flow_layout',
        'vu1_dials_gui.widgets.settings_dialog',
        'vu1_dials_gui.aida64',
        # Optional dependencies — included if installed
        'cryptography',
        'cryptography.fernet',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'pytest',
        'ruff',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='VU1-DIALs-GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # No console window — GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='icon.ico',      # Uncomment if you have an .ico file
)
