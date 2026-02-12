"""Tests for the value mapping logic (sensor value → dial 0-100)."""

from vu1_dials_gui.utils import map_value_to_range


class TestMapValueToRange:
    """Test map_value_to_range — the core logic converting a raw sensor
    reading to a 0-100 percentage for the physical dial.
    """

    # ── Normal cases ──────────────────────────────────────────────────

    def test_middle_of_range(self):
        assert map_value_to_range(50, 0, 100) == 50.0

    def test_at_minimum(self):
        assert map_value_to_range(0, 0, 100) == 0.0

    def test_at_maximum(self):
        assert map_value_to_range(100, 0, 100) == 100.0

    def test_quarter(self):
        assert map_value_to_range(25, 0, 100) == 25.0

    def test_custom_range(self):
        # 60°C in a 20-100°C range → (60-20)/(100-20)*100 = 50%
        assert map_value_to_range(60, 20, 100) == 50.0

    def test_negative_range(self):
        # 0 in a -50 to 50 range → 50%
        assert map_value_to_range(0, -50, 50) == 50.0

    def test_small_range(self):
        # 55 in a 50-60 range → 50%
        assert map_value_to_range(55, 50, 60) == 50.0

    def test_large_values(self):
        assert map_value_to_range(5000, 0, 10000) == 50.0

    # ── Clamping ──────────────────────────────────────────────────────

    def test_below_minimum_clamps_to_zero(self):
        assert map_value_to_range(-10, 0, 100) == 0.0

    def test_above_maximum_clamps_to_100(self):
        assert map_value_to_range(150, 0, 100) == 100.0

    def test_far_below_clamps(self):
        assert map_value_to_range(-1000, 0, 100) == 0.0

    def test_far_above_clamps(self):
        assert map_value_to_range(99999, 0, 100) == 100.0

    # ── Edge cases ────────────────────────────────────────────────────

    def test_zero_division_returns_zero(self):
        """When min == max, should return 0 instead of crashing."""
        assert map_value_to_range(50, 50, 50) == 0.0

    def test_float_values(self):
        assert map_value_to_range(37.5, 0.0, 75.0) == 50.0

    def test_very_small_range(self):
        assert map_value_to_range(0.5, 0.0, 1.0) == 50.0

    # ── Precision ─────────────────────────────────────────────────────

    def test_one_third(self):
        result = map_value_to_range(1, 0, 3)
        assert abs(result - 33.333) < 0.01

    def test_two_thirds(self):
        result = map_value_to_range(2, 0, 3)
        assert abs(result - 66.666) < 0.01
