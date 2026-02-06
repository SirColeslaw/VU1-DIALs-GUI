"""
VU1 Server REST API client.

Provides methods for all interactions with the VU1 dial hardware
server, including dial control, image management, and backlight settings.

Authentication is sent both via HTTP header (``X-API-Key``) and as a
query parameter (``key``) for backward compatibility with servers that
only support query-parameter authentication.
"""

import logging
from typing import Any

import requests

from ..config.crypto import mask_api_key
from ..constants import (
    API_BASE_PATH,
    API_KEY_HEADER,
    ENDPOINT_DIAL_BACKLIGHT,
    ENDPOINT_DIAL_EASING,
    ENDPOINT_DIAL_IMAGE_GET,
    ENDPOINT_DIAL_IMAGE_SET,
    ENDPOINT_DIAL_LIST,
    ENDPOINT_DIAL_NAME,
    ENDPOINT_DIAL_SET,
    ENDPOINT_DIAL_STATUS,
    REQUEST_TIMEOUT,
    RGB_API_MAX,
    RGB_MAX,
    SHUTDOWN_TIMEOUT,
)

logger = logging.getLogger(__name__)


class VU1ApiClient:
    """HTTP client for the VU1 Server REST API.

    Handles all communication with the VU1 dial hardware server,
    including authentication, error handling, and response parsing.

    The API key is sent via the ``X-API-Key`` HTTP header and also
    as a ``key`` query parameter for backward compatibility.
    """

    def __init__(self, server_address: str, api_key: str) -> None:
        """Initialize the API client.

        Args:
            server_address: Base URL of the VU1 server (e.g. http://localhost:5340).
            api_key: Authentication key for API requests.
        """
        self.server_address: str = server_address
        self.api_key: str = api_key

    def _build_url(self, endpoint: str, **kwargs: str) -> str:
        """Build a full API URL from an endpoint template.

        Args:
            endpoint: The endpoint path template (e.g. 'dial/{dial_id}/set').
            **kwargs: Values to format into the endpoint template.

        Returns:
            The complete URL string.
        """
        return f"{self.server_address}{API_BASE_PATH}/{endpoint.format(**kwargs)}"

    def _auth_headers(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        """Build request headers including the API key authentication header.

        Args:
            extra: Additional headers to merge.

        Returns:
            A headers dictionary with authentication and any extras.
        """
        hdrs: dict[str, str] = {API_KEY_HEADER: self.api_key}
        if extra:
            hdrs.update(extra)
        return hdrs

    def _get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: int = REQUEST_TIMEOUT,
        **url_kwargs: str,
    ) -> requests.Response:
        """Send an authenticated GET request to the API.

        The API key is sent both as an ``X-API-Key`` header and as
        a ``key`` query parameter for backward compatibility.

        Args:
            endpoint: The endpoint path template.
            params: Additional query parameters.
            headers: Additional HTTP headers.
            timeout: Request timeout in seconds.
            **url_kwargs: Values to format into the endpoint template.

        Returns:
            The HTTP response object.

        Raises:
            requests.RequestException: On any HTTP error.
        """
        url = self._build_url(endpoint, **url_kwargs)
        # Query param kept for backward compat with servers that don't read headers
        request_params: dict[str, Any] = {"key": self.api_key}
        if params:
            request_params.update(params)
        return requests.get(
            url,
            params=request_params,
            headers=self._auth_headers(headers),
            timeout=timeout,
        )

    def _post(
        self,
        endpoint: str,
        files: dict[str, Any] | None = None,
        timeout: int = REQUEST_TIMEOUT,
        **url_kwargs: str,
    ) -> requests.Response:
        """Send an authenticated POST request to the API.

        The API key is sent both as an ``X-API-Key`` header and as
        a ``key`` query parameter for backward compatibility.

        Args:
            endpoint: The endpoint path template.
            files: Files to upload (multipart form data).
            timeout: Request timeout in seconds.
            **url_kwargs: Values to format into the endpoint template.

        Returns:
            The HTTP response object.

        Raises:
            requests.RequestException: On any HTTP error.
        """
        url = self._build_url(endpoint, **url_kwargs)
        params: dict[str, Any] = {"key": self.api_key}
        return requests.post(
            url,
            params=params,
            files=files,
            headers=self._auth_headers(),
            timeout=timeout,
        )

    def test_connection(self, server_address: str, api_key: str) -> requests.Response:
        """Test connectivity to the VU1 server with given credentials.

        Args:
            server_address: Server URL to test.
            api_key: API key to validate.

        Returns:
            The HTTP response from the dial list endpoint.

        Raises:
            requests.ConnectionError: If the server is unreachable.
            requests.Timeout: If the request times out.
            requests.RequestException: On other HTTP errors.
        """
        url = f"{server_address}{API_BASE_PATH}/{ENDPOINT_DIAL_LIST}"
        logger.info(
            "Testing connection to %s with key %s",
            server_address, mask_api_key(api_key),
        )
        response = requests.get(
            url,
            params={"key": api_key},
            headers={API_KEY_HEADER: api_key},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response

    def get_dial_list(self) -> list[dict[str, Any]]:
        """Fetch the list of all connected dials.

        Returns:
            A list of dial info dictionaries, each containing at least 'uid'.

        Raises:
            ValueError: If the API response format is invalid.
            requests.RequestException: On HTTP errors.
        """
        response = self._get(ENDPOINT_DIAL_LIST)
        response.raise_for_status()
        response_data = response.json()

        dials = response_data.get("data", [])
        if not isinstance(dials, list):
            raise ValueError(f"Invalid API response format: {response_data}")
        return dials

    def get_dial_status(self, dial_id: str) -> dict[str, Any] | None:
        """Fetch the status of a specific dial.

        Args:
            dial_id: The unique identifier of the dial.

        Returns:
            The parsed JSON response, or None on failure.
        """
        try:
            response = self._get(
                ENDPOINT_DIAL_STATUS,
                headers={"Accept": "application/json"},
                dial_id=dial_id,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error("Error fetching status for dial %s: %s", dial_id, e)
            return None

    def get_dial_image(self, dial_id: str) -> bytes | None:
        """Fetch the current image of a specific dial.

        Args:
            dial_id: The unique identifier of the dial.

        Returns:
            Raw PNG image bytes, or None if unavailable.
        """
        try:
            response = self._get(ENDPOINT_DIAL_IMAGE_GET, dial_id=dial_id)
            response.raise_for_status()
            if response.headers.get("Content-Type") == "image/png":
                return response.content
            return None
        except requests.RequestException as e:
            logger.error("Error fetching image for dial %s: %s", dial_id, e)
            return None

    def set_dial_image(self, dial_id: str, image_file: Any) -> bool:
        """Upload a new image to a dial.

        Args:
            dial_id: The unique identifier of the dial.
            image_file: A file-like object containing the image data.

        Returns:
            True if the image was set successfully, False otherwise.
        """
        try:
            response = self._post(
                ENDPOINT_DIAL_IMAGE_SET,
                files={"imgfile": image_file},
                dial_id=dial_id,
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error("Error setting image for dial %s: %s", dial_id, e)
            return False

    def set_dial_value(self, dial_id: str, value: float) -> bool:
        """Set the display value of a dial (0-100).

        Args:
            dial_id: The unique identifier of the dial.
            value: The value to display, clamped to 0-100 range.

        Returns:
            True if the value was set successfully, False otherwise.
        """
        try:
            response = self._get(
                ENDPOINT_DIAL_SET,
                params={"value": value},
                dial_id=dial_id,
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error("Error setting value for dial %s: %s", dial_id, e)
            return False

    def set_dial_name(self, dial_id: str, name: str) -> bool:
        """Set the display name of a dial.

        Args:
            dial_id: The unique identifier of the dial.
            name: The new name for the dial.

        Returns:
            True if the name was set successfully, False otherwise.
        """
        try:
            response = self._get(
                ENDPOINT_DIAL_NAME,
                params={"name": name},
                dial_id=dial_id,
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error("Error setting name for dial %s: %s", dial_id, e)
            return False

    def set_backlight(self, dial_id: str, red: int, green: int, blue: int) -> bool:
        """Set the backlight color of a dial.

        RGB values are converted from 0-255 range to 0-100 percentage
        for the API.

        Args:
            dial_id: The unique identifier of the dial.
            red: Red channel value (0-255).
            green: Green channel value (0-255).
            blue: Blue channel value (0-255).

        Returns:
            True if the backlight was set successfully, False otherwise.
        """
        try:
            red_pct = int((red / RGB_MAX) * RGB_API_MAX)
            green_pct = int((green / RGB_MAX) * RGB_API_MAX)
            blue_pct = int((blue / RGB_MAX) * RGB_API_MAX)

            response = self._get(
                ENDPOINT_DIAL_BACKLIGHT,
                params={"red": red_pct, "green": green_pct, "blue": blue_pct},
                dial_id=dial_id,
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error("Error setting backlight for dial %s: %s", dial_id, e)
            return False

    def set_dial_easing(self, dial_id: str, period: int, step: int) -> bool:
        """Configure the easing parameters for smooth dial movement.

        Args:
            dial_id: The unique identifier of the dial.
            period: Update period in milliseconds.
            step: Maximum step size in percent per update.

        Returns:
            True if the easing was set successfully, False otherwise.
        """
        try:
            response = self._get(
                ENDPOINT_DIAL_EASING,
                params={"period": period, "step": step},
                dial_id=dial_id,
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            logger.error("Error setting easing for dial %s: %s", dial_id, e)
            return False

    def shutdown_dial(self, dial_id: str) -> None:
        """Shut down a dial by setting value to 0 and turning off backlight.

        Uses a short timeout to avoid blocking during application exit.

        Args:
            dial_id: The unique identifier of the dial.
        """
        try:
            self._get(
                ENDPOINT_DIAL_SET,
                params={"value": 0},
                timeout=SHUTDOWN_TIMEOUT,
                dial_id=dial_id,
            )
            self._get(
                ENDPOINT_DIAL_BACKLIGHT,
                params={"red": 0, "green": 0, "blue": 0},
                timeout=SHUTDOWN_TIMEOUT,
                dial_id=dial_id,
            )
        except requests.exceptions.Timeout:
            logger.debug("Timeout during shutdown of dial %s (expected)", dial_id)
        except requests.RequestException as e:
            logger.error("Error shutting down dial %s: %s", dial_id, e)

    def fetch_dial_details(self, dial_id: str) -> dict[str, Any]:
        """Fetch complete details (status + image) for a single dial.

        Args:
            dial_id: The unique identifier of the dial.

        Returns:
            A dictionary with 'status' and 'image' keys.
        """
        details: dict[str, Any] = {}
        details["status"] = self.get_dial_status(dial_id)
        details["image"] = self.get_dial_image(dial_id)
        return details
