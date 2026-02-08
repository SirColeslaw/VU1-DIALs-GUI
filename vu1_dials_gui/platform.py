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
HAS_AIDA64: bool = False

if IS_WINDOWS:
    try:
        import winreg  # noqa: F401
        HAS_WINREG = True
    except ImportError:
        pass

    try:
        from python_aida64 import getData  # noqa: F401
        HAS_AIDA64 = True
    except ImportError:
        pass
else:
    # On non-Windows platforms, try importing AIDA64 anyway (unlikely but possible)
    try:
        from python_aida64 import getData  # noqa: F401
        HAS_AIDA64 = True
    except ImportError:
        pass
