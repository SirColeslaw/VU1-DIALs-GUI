"""Tests for the VU1 API client (all HTTP calls mocked)."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from vu1_dials_gui.api.client import VU1ApiClient


@pytest.fixture
def client():
    """Return an API client with test credentials."""
    return VU1ApiClient(
        server_address="http://localhost:5340",
        api_key="test-key-123",
    )


# ── URL building ──────────────────────────────────────────────────────


class TestBuildUrl:
    def test_simple_endpoint(self, client):
        url = client._build_url("dial/list")
        assert url == "http://localhost:5340/api/v0/dial/list"

    def test_endpoint_with_params(self, client):
        url = client._build_url("dial/{dial_id}/set", dial_id="abc-123")
        assert url == "http://localhost:5340/api/v0/dial/abc-123/set"


# ── Auth headers ──────────────────────────────────────────────────────


class TestAuthHeaders:
    def test_contains_api_key_header(self, client):
        headers = client._auth_headers()
        assert "X-API-Key" in headers
        assert headers["X-API-Key"] == "test-key-123"

    def test_merges_extra_headers(self, client):
        headers = client._auth_headers({"Accept": "application/json"})
        assert headers["X-API-Key"] == "test-key-123"
        assert headers["Accept"] == "application/json"

    def test_no_extra_headers(self, client):
        headers = client._auth_headers(None)
        assert headers == {"X-API-Key": "test-key-123"}


# ── GET requests ──────────────────────────────────────────────────────


class TestGetRequests:
    @patch("vu1_dials_gui.api.client.requests.get")
    def test_get_sends_auth_header_and_query_param(self, mock_get, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        client._get("dial/list")

        mock_get.assert_called_once()
        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs["params"]["key"] == "test-key-123"
        assert call_kwargs.kwargs["headers"]["X-API-Key"] == "test-key-123"

    @patch("vu1_dials_gui.api.client.requests.get")
    def test_get_merges_extra_params(self, mock_get, client):
        mock_resp = MagicMock()
        mock_get.return_value = mock_resp

        client._get("dial/{dial_id}/set", params={"value": 50}, dial_id="d1")

        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs["params"]["value"] == 50
        assert call_kwargs.kwargs["params"]["key"] == "test-key-123"
        assert "d1" in call_kwargs.args[0]


# ── POST requests ─────────────────────────────────────────────────────


class TestPostRequests:
    @patch("vu1_dials_gui.api.client.requests.post")
    def test_post_sends_auth_header(self, mock_post, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_post.return_value = mock_resp

        client._post("dial/{dial_id}/image/set", dial_id="d1")

        call_kwargs = mock_post.call_args
        assert call_kwargs.kwargs["headers"]["X-API-Key"] == "test-key-123"
        assert call_kwargs.kwargs["params"]["key"] == "test-key-123"


# ── get_dial_list ─────────────────────────────────────────────────────


class TestGetDialList:
    @patch("vu1_dials_gui.api.client.requests.get")
    def test_returns_list_of_dials(self, mock_get, client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "data": [{"uid": "dial-001"}, {"uid": "dial-002"}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        dials = client.get_dial_list()
        assert len(dials) == 2
        assert dials[0]["uid"] == "dial-001"

    @patch("vu1_dials_gui.api.client.requests.get")
    def test_raises_on_invalid_format(self, mock_get, client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"data": "not-a-list"}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        with pytest.raises(ValueError, match="Invalid API response"):
            client.get_dial_list()


# ── set_dial_value ────────────────────────────────────────────────────


class TestSetDialValue:
    @patch("vu1_dials_gui.api.client.requests.get")
    def test_set_value_success(self, mock_get, client):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = client.set_dial_value("dial-001", 75.5)
        assert result is True

        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs["params"]["value"] == 75.5

    @patch("vu1_dials_gui.api.client.requests.get")
    def test_set_value_failure(self, mock_get, client):
        mock_get.side_effect = requests.ConnectionError("Server down")

        result = client.set_dial_value("dial-001", 50)
        assert result is False


# ── set_dial_name ─────────────────────────────────────────────────────


class TestSetDialName:
    @patch("vu1_dials_gui.api.client.requests.get")
    def test_set_name_success(self, mock_get, client):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = client.set_dial_name("dial-001", "CPU Temp")
        assert result is True

    @patch("vu1_dials_gui.api.client.requests.get")
    def test_set_name_failure(self, mock_get, client):
        mock_get.side_effect = requests.Timeout()

        result = client.set_dial_name("dial-001", "CPU Temp")
        assert result is False


# ── set_backlight ─────────────────────────────────────────────────────


class TestSetBacklight:
    @patch("vu1_dials_gui.api.client.requests.get")
    def test_converts_rgb_to_percentage(self, mock_get, client):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        client.set_backlight("dial-001", red=255, green=128, blue=0)

        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs["params"]
        assert params["red"] == 100  # 255/255 * 100
        assert params["green"] == 50  # 128/255 * 100 ≈ 50
        assert params["blue"] == 0

    @patch("vu1_dials_gui.api.client.requests.get")
    def test_backlight_failure(self, mock_get, client):
        mock_get.side_effect = requests.ConnectionError()

        result = client.set_backlight("dial-001", 255, 255, 255)
        assert result is False


# ── set_dial_easing ───────────────────────────────────────────────────


class TestSetDialEasing:
    @patch("vu1_dials_gui.api.client.requests.get")
    def test_easing_success(self, mock_get, client):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = client.set_dial_easing("dial-001", period=100, step=10)
        assert result is True

        call_kwargs = mock_get.call_args
        params = call_kwargs.kwargs["params"]
        assert params["period"] == 100
        assert params["step"] == 10


# ── set_dial_image ────────────────────────────────────────────────────


class TestSetDialImage:
    @patch("vu1_dials_gui.api.client.requests.post")
    def test_image_upload_success(self, mock_post, client):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        fake_file = MagicMock()
        result = client.set_dial_image("dial-001", fake_file)
        assert result is True

    @patch("vu1_dials_gui.api.client.requests.post")
    def test_image_upload_failure(self, mock_post, client):
        mock_post.side_effect = requests.ConnectionError()

        result = client.set_dial_image("dial-001", MagicMock())
        assert result is False


# ── get_dial_image ────────────────────────────────────────────────────


class TestGetDialImage:
    @patch("vu1_dials_gui.api.client.requests.get")
    def test_returns_png_bytes(self, mock_get, client):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.headers = {"Content-Type": "image/png"}
        mock_resp.content = b"\x89PNG\r\n\x1a\n"
        mock_get.return_value = mock_resp

        result = client.get_dial_image("dial-001")
        assert result == b"\x89PNG\r\n\x1a\n"

    @patch("vu1_dials_gui.api.client.requests.get")
    def test_returns_none_for_non_png(self, mock_get, client):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_get.return_value = mock_resp

        result = client.get_dial_image("dial-001")
        assert result is None

    @patch("vu1_dials_gui.api.client.requests.get")
    def test_returns_none_on_error(self, mock_get, client):
        mock_get.side_effect = requests.ConnectionError()

        result = client.get_dial_image("dial-001")
        assert result is None


# ── shutdown_dial ─────────────────────────────────────────────────────


class TestShutdownDial:
    @patch("vu1_dials_gui.api.client.requests.get")
    def test_shutdown_sets_zero_and_off(self, mock_get, client):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        client.shutdown_dial("dial-001")

        assert mock_get.call_count == 2
        # First call: set value to 0
        first_call = mock_get.call_args_list[0]
        assert first_call.kwargs["params"]["value"] == 0
        # Second call: backlight off
        second_call = mock_get.call_args_list[1]
        assert second_call.kwargs["params"]["red"] == 0

    @patch("vu1_dials_gui.api.client.requests.get")
    def test_shutdown_handles_timeout(self, mock_get, client):
        mock_get.side_effect = requests.exceptions.Timeout()

        # Should not raise
        client.shutdown_dial("dial-001")


# ── test_connection ───────────────────────────────────────────────────


class TestTestConnection:
    @patch("vu1_dials_gui.api.client.requests.get")
    def test_connection_success(self, mock_get, client):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        resp = client.test_connection("http://test:5340", "key-abc")

        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs["headers"]["X-API-Key"] == "key-abc"
        assert call_kwargs.kwargs["params"]["key"] == "key-abc"

    @patch("vu1_dials_gui.api.client.requests.get")
    def test_connection_raises_on_failure(self, mock_get, client):
        mock_get.side_effect = requests.ConnectionError("unreachable")

        with pytest.raises(requests.ConnectionError):
            client.test_connection("http://test:5340", "key-abc")
