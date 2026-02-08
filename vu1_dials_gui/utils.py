"""
Utility functions for the VU1 DIALs GUI.

Contains pure logic functions that are independent of the GUI framework,
making them easy to test without PyQt6.
"""


def map_value_to_range(value: float, min_value: float, max_value: float) -> float:
    """Map a sensor value to the 0-100 dial range.

    Converts a raw sensor reading to a percentage based on the
    user-configured minimum and maximum values. The result is
    clamped to the 0-100 range.

    Args:
        value: The raw sensor value.
        min_value: The configured minimum of the sensor range.
        max_value: The configured maximum of the sensor range.

    Returns:
        The mapped value clamped to 0-100.
    """
    try:
        return max(0.0, min(100.0, ((value - min_value) / (max_value - min_value)) * 100))
    except (ZeroDivisionError, TypeError):
        return 0.0
