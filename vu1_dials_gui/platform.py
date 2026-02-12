"""
Platform detection and feature availability.

Provides flags and helpers so the rest of the application can
conditionally enable Windows-only features (autostart via registry,
AIDA64 shared memory) without crashing on Linux or macOS.
"""

import sys

IS_WINDOWS: bool = sys.platform == "win32"
IS_LINUX: bool = sys.platform.startswith("linux")
IS_MACOS: bool = sys.platform == "darwin"

# Feature flags derived from platform
HAS_WINREG: bool = False
HAS_AIDA64: bool = IS_WINDOWS  # AIDA64 shared memory is Windows-only

if IS_WINDOWS:
    try:
        import winreg  # noqa: F401
        HAS_WINREG = True
    except ImportError:
        pass
