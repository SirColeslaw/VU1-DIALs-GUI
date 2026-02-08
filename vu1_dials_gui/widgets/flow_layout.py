"""
Flow layout implementation for responsive dial widget arrangement.

Provides a custom QLayout that arranges widgets in a flowing grid,
wrapping to the next row when the container width is exceeded.
"""

from PyQt6.QtCore import QPoint, QRect, QSize, Qt
from PyQt6.QtWidgets import QLayout, QLayoutItem, QWidget

from ..constants import FLOW_LAYOUT_SPACING_X, FLOW_LAYOUT_SPACING_Y


class FlowLayout(QLayout):
    """A layout that arranges widgets in a flowing, wrapping grid.

    Widgets are placed left-to-right and wrap to the next row when
    the available width is exceeded. Supports dynamic resizing.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the flow layout.

        Args:
            parent: Parent widget for the layout.
        """
        super().__init__(parent)
        self._items: list[QLayoutItem] = []
        self._rows: list[list[QLayoutItem]] = []

    def addItem(self, item: QLayoutItem) -> None:
        """Add a layout item to the flow.

        Args:
            item: The layout item to add.
        """
        self._items.append(item)

    def count(self) -> int:
        """Return the number of items in the layout."""
        return len(self._items)

    def itemAt(self, index: int) -> QLayoutItem | None:
        """Return the item at the given index, or None if out of range.

        Args:
            index: Zero-based index of the item.
        """
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int) -> QLayoutItem | None:
        """Remove and return the item at the given index.

        Args:
            index: Zero-based index of the item to remove.
        """
        if 0 <= index < len(self._items):
            return self._items.pop(index)
        return None

    def expandingDirections(self) -> Qt.Orientation:
        """Return that this layout does not expand in any direction."""
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        """Return True since this layout's height depends on its width."""
        return True

    def heightForWidth(self, width: int) -> int:
        """Calculate the required height for a given width.

        Args:
            width: The available width in pixels.

        Returns:
            The required height in pixels.
        """
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect) -> None:
        """Set the geometry of all items in the layout.

        Args:
            rect: The available rectangle for layout.
        """
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self) -> QSize:
        """Return the preferred size of the layout."""
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        """Return the minimum size needed to display all items."""
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())
        return size

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        """Perform the actual layout calculation and optional placement.

        Arranges items left-to-right with wrapping. When test_only is True,
        only calculates the required height without moving widgets.

        Algorithm:
            Walk through all items, tracking the current x/y cursor position.
            For each item, compute where its right edge would land (next_x).
            If placing the item would exceed the container width *and* there
            is already content on the current row (line_height > 0), wrap to
            a new row by resetting x and advancing y by the tallest item in
            the completed row plus vertical spacing.  line_height tracks the
            tallest item on the current row so the next row starts below it.

        Args:
            rect: The available rectangle for layout.
            test_only: If True, only calculate height without moving items.

        Returns:
            The total height required for the layout.
        """
        x = rect.x()
        y = rect.y()
        line_height = 0  # Height of the tallest item in the current row
        self._rows = []
        current_row: list[QLayoutItem] = []

        for item in self._items:
            # Calculate where the right edge of this item would be
            next_x = x + item.sizeHint().width() + FLOW_LAYOUT_SPACING_X

            # Wrap to a new row if the item overflows the container width.
            # The "line_height > 0" guard ensures the first item on a row
            # is always placed even if it is wider than the container.
            if next_x - FLOW_LAYOUT_SPACING_X > rect.right() and line_height > 0:
                self._rows.append(current_row)
                current_row = []
                x = rect.x()
                y = y + line_height + FLOW_LAYOUT_SPACING_Y
                next_x = x + item.sizeHint().width() + FLOW_LAYOUT_SPACING_X
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())
            current_row.append(item)

        if current_row:
            self._rows.append(current_row)

        return y + line_height
