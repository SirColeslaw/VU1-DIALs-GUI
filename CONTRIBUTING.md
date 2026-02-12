# Contributing to VU1 DIALs GUI

Thank you for your interest in contributing! This guide covers the developer
setup, project structure, and coding standards.

## Developer Setup

### Prerequisites

- Python 3.10 or later
- A VU1 Server instance (for integration testing)
- (Optional) AIDA64 with Shared Memory enabled (Windows only)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/SirColeslaw/VU1-DIALs-GUI.git
cd VU1-DIALs-GUI

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows

# Install runtime + dev dependencies
pip install -e ".[dev,crypto]"

# Run the test suite
pytest -v

# Run the linter
ruff check .
ruff format --check .
```

### Optional Dependencies

| Extra     | Install command                      | Purpose                                    |
|-----------|--------------------------------------|--------------------------------------------|
| `crypto`  | `pip install -e ".[crypto]"`         | Fernet encryption for API key at rest      |
| `aida64`  | `pip install -e ".[aida64]"`         | AIDA64 shared-memory integration (Windows) |
| `dev`     | `pip install -e ".[dev]"`            | pytest + ruff + cryptography               |

## Project Structure

```
VU1-DIALs-GUI/
├── vu1_dials_gui/               # Main package
│   ├── __init__.py              # Package metadata (__version__)
│   ├── __main__.py              # Entry point (logging setup, app launch)
│   ├── constants.py             # All hardcoded values in one place
│   ├── main_window.py           # Main QMainWindow controller
│   ├── platform.py              # OS detection & feature-availability flags
│   ├── utils.py                 # Pure logic functions (no Qt dependency)
│   ├── validation.py            # Input sanitization & validation
│   ├── api/
│   │   ├── __init__.py
│   │   └── client.py            # VU1 Server REST API client
│   ├── config/
│   │   ├── __init__.py
│   │   ├── crypto.py            # API key encryption (Fernet + base64)
│   │   └── settings.py          # JSON settings persistence
│   └── widgets/
│       ├── __init__.py
│       ├── dial_widget.py       # Single-dial control widget
│       ├── flow_layout.py       # Responsive wrapping grid layout
│       └── settings_dialog.py   # Application settings dialog
├── tests/                       # Unit tests (pytest)
│   ├── conftest.py              # Shared fixtures
│   ├── test_api_client.py
│   ├── test_constants.py
│   ├── test_crypto.py
│   ├── test_settings.py
│   ├── test_validation.py
│   └── test_value_mapping.py
├── .github/workflows/ci.yml    # GitHub Actions CI pipeline
├── pyproject.toml               # Build config, dependencies, tool settings
├── requirements.txt             # Simple pip install alternative
└── vu1-dials-gui.py             # Legacy entry point (thin wrapper)
```

## Coding Standards

### Style

- **Formatter / Linter**: [Ruff](https://docs.astral.sh/ruff/) — runs in CI
- **Line length**: 100 characters max
- **Target version**: Python 3.10+
- **Imports**: sorted by isort (enforced by Ruff `I` rules)

### Type Hints

All public functions and methods must have type annotations:

```python
def map_value_to_range(value: float, min_value: float, max_value: float) -> float:
    ...
```

### Docstrings

Use Google-style docstrings for all public classes and functions:

```python
def set_backlight(self, dial_id: str, red: int, green: int, blue: int) -> bool:
    """Set the backlight color of a dial.

    Args:
        dial_id: The unique identifier of the dial.
        red: Red channel value (0-255).
        green: Green channel value (0-255).
        blue: Blue channel value (0-255).

    Returns:
        True if the backlight was set successfully, False otherwise.
    """
```

### Constants

All magic numbers and hardcoded strings belong in `constants.py`. Never
inline values like port numbers, timeout durations, or RGB ranges directly
in business logic.

### Logging

Use `logging.getLogger(__name__)` — never use `print()` for debug output.
Ruff's `T20` rule will catch stray `print()` calls.

### Platform Safety

Windows-only features (winreg, AIDA64) must be guarded with the flags in
`vu1_dials_gui/platform.py`:

```python
from .platform import HAS_WINREG, HAS_AIDA64

if HAS_WINREG:
    import winreg
    # ... Windows-only code
```

## Testing

### Running Tests

```bash
# All tests
pytest -v

# Specific test file
pytest tests/test_validation.py -v

# With coverage (if installed)
pytest --cov=vu1_dials_gui -v
```

### Writing Tests

- Tests live in the `tests/` directory, one file per module
- Use `unittest.mock` for external dependencies (HTTP calls, file I/O)
- Shared fixtures go in `tests/conftest.py`
- Avoid importing PyQt6 in tests — extract pure logic to `utils.py` if needed
- Use `assert` statements (Ruff's `S101` rule is suppressed for `tests/`)

### CI Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push
and PR to `main`:

1. **Lint**: `ruff check .` + `ruff format --check .`
2. **Test**: `pytest -v` on Python 3.10, 3.11, and 3.12

## Pull Request Workflow

1. Fork the repository and create a feature branch
2. Make your changes with tests
3. Run `ruff check .` and `pytest -v` locally
4. Open a PR against `main`
5. Ensure CI passes before requesting review

## Architecture Notes

### Key Design Patterns

- **MVC-like separation**: `main_window.py` acts as controller, widgets
  are views, `SettingsManager` + API client handle the model layer
- **Signal/slot pattern**: PyQt6 signals connect UI events to controller methods
- **Graceful degradation**: Missing optional dependencies (cryptography,
  python_aida64, winreg) are handled at import time with fallback behavior

### Data Flow

```
AIDA64 Shared Memory → python_aida64 → main_window (poll timer)
  → map_value_to_range() → VU1ApiClient → VU1 Server → Hardware Dial
```

Sensor data is polled every second (`SENSOR_UPDATE_INTERVAL_MS`), mapped
from the user-configured [min, max] range to the dial's 0–100% scale,
and sent to the VU1 Server via its REST API.
