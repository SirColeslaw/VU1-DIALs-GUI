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
        # Linear interpolation: shift value so that min_value becomes 0,
        # divide by the range width to get a 0.0–1.0 fraction, then scale
        # to 0–100 for the VU1 dial's percentage input.
        # Clamp to [0, 100] so out-of-range sensor readings are safe.
        fraction = (value - min_value) / (max_value - min_value)
        return max(0.0, min(100.0, fraction * 100))
    except (ZeroDivisionError, TypeError):
        return 0.0
