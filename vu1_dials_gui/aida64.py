"""
Read AIDA64 sensor data from Windows shared memory.

AIDA64 exposes sensor readings (temperatures, fan speeds, voltages, etc.)
via a named shared memory region called ``AIDA64_SensorValues``.  This
module reads that region, parses the XML payload, and returns a structured
dictionary grouped by sensor category.

Based on python_aida64 by gwy15 (https://github.com/gwy15/python_aida64),
licensed under the WTFPL.  Integrated here to avoid an external dependency
on an archived, non-PyPI package.

Windows only — on other platforms, :func:`get_data` returns an empty dict.
"""

from __future__ import annotations

import logging
import sys
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)

# Shared-memory tags are a Windows-only mmap feature.
_IS_WINDOWS = sys.platform == "win32"


def _read_raw_bytes(length: int) -> bytes:
    """Read *length* bytes from the AIDA64 shared-memory region."""
    import mmap

    with mmap.mmap(
        -1,
        length,
        tagname="AIDA64_SensorValues",
        access=mmap.ACCESS_READ,
    ) as mm:
        return mm.read()


def _decode(raw: bytes) -> str:
    """Decode bytes trying several encodings in order."""
    for encoding in (sys.getdefaultencoding(), "utf-8", "gbk"):
        try:
            return raw.decode(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode()


def get_xml_raw_data() -> str | None:
    """Return the raw XML string from AIDA64 shared memory.

    Uses a binary search over buffer sizes (2 KB – 10 KB) to find the
    smallest buffer that contains a complete, null-terminated payload.

    Returns ``None`` if the shared memory cannot be read.
    """
    options = [100 * i for i in range(20, 100)]  # 2 000 … 9 900
    low = 0
    high = len(options) - 1

    while low < high:
        mid = (low + high) // 2
        try:
            raw = _read_raw_bytes(options[mid])
            if raw[-1] == 0:  # complete payload
                decoded = _decode(raw.rstrip(b"\x00"))
                return f"<root>{decoded}</root>"
            else:  # buffer too small
                low = mid + 1
        except PermissionError:  # buffer too large
            high = mid
    return None


def get_data() -> dict:
    """Return AIDA64 sensor data grouped by category.

    Example return value::

        {
            "temp": [
                {"id": "TCPU", "label": "CPU", "value": "45"},
                ...
            ],
            "fan": [
                {"id": "FCPU", "label": "CPU", "value": "906"},
                ...
            ],
        }

    Returns an empty dict when not running on Windows or when AIDA64
    shared memory is unavailable.
    """
    if not _IS_WINDOWS:
        return {}

    try:
        xml = get_xml_raw_data()
        if xml is None:
            return {}

        tree = ET.fromstring(xml)  # noqa: S314 — data from local shared memory, not untrusted
        data: dict[str, list[dict[str, str]]] = {}
        for item in tree:
            if item.tag not in data:
                data[item.tag] = []
            data[item.tag].append(
                {key: item.find(key).text for key in ("id", "label", "value")}
            )
        return data
    except Exception:
        logger.debug("Could not read AIDA64 shared memory", exc_info=True)
        return {}
