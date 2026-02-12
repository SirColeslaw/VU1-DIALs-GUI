# Changelog

All notable changes to VU1 DIALs GUI will be documented in this file.

## [1.1.0] - 2026-02-12

Major refactoring and modernization of the codebase. The application has been
restructured from a single monolithic script into a clean, modular Python
package with proper testing, CI/CD, and security improvements.

### Added

- **Modular package structure** — reorganized into `vu1_dials_gui/` with
  dedicated sub-packages for API (`api/`), configuration (`config/`), and
  UI components (`widgets/`).
- **Integrated AIDA64 shared memory reader** (`vu1_dials_gui/aida64.py`) —
  reads sensor data directly from AIDA64 shared memory, removing the need
  for the external `python_aida64` package (which is archived and not on PyPI).
- **API key encryption at rest** — API keys are encrypted using Fernet
  (via `cryptography` library) before being saved to disk, with automatic
  fallback to base64 obfuscation when cryptography is not installed.
- **Input validation and sanitization** — all user inputs (dial names, server
  addresses, API keys, value ranges, RGB values) are validated before use.
- **Cross-platform compatibility** — platform detection module with feature
  flags (`IS_WINDOWS`, `IS_LINUX`, `IS_MACOS`, `HAS_WINREG`, `HAS_AIDA64`)
  so the app can run on Linux and macOS without crashing on Windows-only features.
- **Comprehensive test suite** — 122 unit tests covering the API client,
  settings persistence, encryption, validation, value mapping, and constants.
- **CI pipeline** (GitHub Actions) — automated linting (Ruff) and testing
  (Python 3.10/3.11/3.12) on every push and PR to main.
- **Release pipeline** (GitHub Actions) — automated Windows `.exe` build via
  PyInstaller and GitHub Release creation on version tags. Tags containing `-`
  (e.g. `v1.1.0-beta.1`) are automatically marked as pre-releases.
- **PyInstaller spec file** (`vu1-dials-gui.spec`) — configured for
  single-file Windows executable builds with all dependencies bundled.
- **Modern Python packaging** (`pyproject.toml`) — proper project metadata,
  dependency declarations, Ruff linter configuration, and entry points.
- **Contributing guide** (`CONTRIBUTING.md`) — documentation for project
  structure, coding standards, and contribution workflow.
- `.gitignore` for Python projects.
- `requirements.txt` for quick dependency installation.

### Changed

- **Entry point** — `vu1-dials-gui.py` is now a thin wrapper that delegates
  to `vu1_dials_gui.__main__:main`. All application logic lives in the package.
- **Centralized constants** — magic numbers and strings moved to
  `vu1_dials_gui/constants.py` (API paths, default values, UI dimensions,
  validation limits).
- **Structured API client** (`vu1_dials_gui/api/client.py`) — clean class
  with typed methods for all VU1 Server endpoints, replacing inline
  `requests` calls scattered throughout the old monolithic script.
- **Settings management** (`vu1_dials_gui/config/settings.py`) — dedicated
  manager class with JSON persistence, transparent API key encryption, and
  cross-platform config directory handling.

### Removed

- **External `python_aida64` dependency** — replaced by the integrated
  shared memory reader. This was the main blocker for automated builds since
  the package was never published to PyPI.

## [1.0.0] - 2024-12-01

### Added

- Initial release with single-file `vu1-dials-gui.py`.
- PyQt6-based GUI for controlling Streacom VU1 dials.
- AIDA64 sensor data integration via shared memory.
- Dial management: image upload, backlight RGB control, easing parameters.
- Settings and assignments persistence via JSON files.
- System tray support with autostart option (Windows).
